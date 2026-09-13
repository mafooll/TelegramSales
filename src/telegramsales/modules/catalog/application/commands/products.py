from dataclasses import dataclass

from telegramsales.modules.catalog.application.access import ensure_can_manage
from telegramsales.modules.catalog.application.exceptions import (
    BrandNotFoundError,
    CatalogNotFoundError,
    CategoryNotFoundError,
    ProductNotFoundError,
)
from telegramsales.modules.catalog.application.ports import ICatalogUnitOfWork
from telegramsales.modules.catalog.contracts import (
    BrandId,
    CatalogId,
    CategoryId,
    ProductId,
)
from telegramsales.modules.catalog.domain.entities import Product
from telegramsales.modules.catalog.domain.enums import MediaKind, MediaLayout
from telegramsales.modules.catalog.domain.services import (
    ensure_can_be_published,
    ensure_category_fits,
)
from telegramsales.modules.catalog.domain.values import Description, Title
from telegramsales.shared.application.access import Actor
from telegramsales.shared.application.clock import IClock
from telegramsales.shared.application.events import IEventPublisher
from telegramsales.shared.domain.money import Money


@dataclass(frozen=True, slots=True)
class CreateProduct:
    catalog_id: CatalogId
    category_id: CategoryId
    title: Title
    description: Description
    price: Money
    brand_id: BrandId | None = None


@dataclass(frozen=True, slots=True)
class RenameProduct:
    product_id: ProductId
    title: Title


@dataclass(frozen=True, slots=True)
class DescribeProduct:
    product_id: ProductId
    description: Description


@dataclass(frozen=True, slots=True)
class RepriceProduct:
    product_id: ProductId
    price: Money
    old_price: Money | None = None


@dataclass(frozen=True, slots=True)
class MoveProduct:
    product_id: ProductId
    catalog_id: CatalogId
    category_id: CategoryId


@dataclass(frozen=True, slots=True)
class RebrandProduct:
    product_id: ProductId
    brand_id: BrandId | None


@dataclass(frozen=True, slots=True)
class PublishProduct:
    product_id: ProductId


@dataclass(frozen=True, slots=True)
class ChangeProductVisibility:
    product_id: ProductId
    is_visible: bool


@dataclass(frozen=True, slots=True)
class ChangeProductStock:
    product_id: ProductId
    is_in_stock: bool


@dataclass(frozen=True, slots=True)
class ChangeMediaLayout:
    product_id: ProductId
    layout: MediaLayout


@dataclass(frozen=True, slots=True)
class DeleteProduct:
    product_id: ProductId


class ProductHandler:
    def __init__(self, uow: ICatalogUnitOfWork) -> None:
        self._uow: ICatalogUnitOfWork = uow

    async def _load(self, uow: ICatalogUnitOfWork, product_id: ProductId) -> Product:
        product = await uow.products.get(product_id)
        if product is None:
            raise ProductNotFoundError(product_id=product_id)
        return product


class CreateProductHandler(ProductHandler):
    def __init__(self, uow: ICatalogUnitOfWork, clock: IClock) -> None:
        super().__init__(uow)
        self._clock: IClock = clock

    async def handle(self, command: CreateProduct, actor: Actor) -> ProductId:
        ensure_can_manage(actor)

        async with self._uow as uow:
            if not await uow.catalogs.get(command.catalog_id):
                raise CatalogNotFoundError(catalog_id=command.catalog_id)

            category = await uow.categories.get(command.category_id)
            if category is None:
                raise CategoryNotFoundError(category_id=command.category_id)
            ensure_category_fits(category, command.catalog_id)

            if command.brand_id is not None and not await uow.brands.get(
                command.brand_id
            ):
                raise BrandNotFoundError(brand_id=command.brand_id)

            product = Product.create(
                product_id=await uow.products.next_id(),
                catalog_id=command.catalog_id,
                category_id=command.category_id,
                title=command.title,
                description=command.description,
                article=await uow.products.next_article(),
                price=command.price,
                now=self._clock.now(),
                brand_id=command.brand_id,
            )
            await uow.products.add(product)

        return product.id


class RenameProductHandler(ProductHandler):
    async def handle(self, command: RenameProduct, actor: Actor) -> None:
        ensure_can_manage(actor)

        async with self._uow as uow:
            product = await self._load(uow, command.product_id)
            product.rename(command.title)
            await uow.products.save(product)


class DescribeProductHandler(ProductHandler):
    async def handle(self, command: DescribeProduct, actor: Actor) -> None:
        ensure_can_manage(actor)

        async with self._uow as uow:
            product = await self._load(uow, command.product_id)
            product.describe(command.description)
            await uow.products.save(product)


class RepriceProductHandler(ProductHandler):
    async def handle(self, command: RepriceProduct, actor: Actor) -> None:
        ensure_can_manage(actor)

        async with self._uow as uow:
            product = await self._load(uow, command.product_id)
            product.reprice(command.price, command.old_price)
            await uow.products.save(product)


class MoveProductHandler(ProductHandler):
    async def handle(self, command: MoveProduct, actor: Actor) -> None:
        ensure_can_manage(actor)

        async with self._uow as uow:
            product = await self._load(uow, command.product_id)

            category = await uow.categories.get(command.category_id)
            if category is None:
                raise CategoryNotFoundError(category_id=command.category_id)
            ensure_category_fits(category, command.catalog_id)

            product.move_to(command.catalog_id, command.category_id)
            await uow.products.save(product)


class RebrandProductHandler(ProductHandler):
    async def handle(self, command: RebrandProduct, actor: Actor) -> None:
        ensure_can_manage(actor)

        async with self._uow as uow:
            product = await self._load(uow, command.product_id)

            if command.brand_id is not None and not await uow.brands.get(
                command.brand_id
            ):
                raise BrandNotFoundError(brand_id=command.brand_id)

            product.rebrand(command.brand_id)
            await uow.products.save(product)


class PublishProductHandler(ProductHandler):
    def __init__(
        self,
        uow: ICatalogUnitOfWork,
        clock: IClock,
        events: IEventPublisher,
    ) -> None:
        super().__init__(uow)
        self._clock: IClock = clock
        self._events: IEventPublisher = events

    async def handle(self, command: PublishProduct, actor: Actor) -> None:
        ensure_can_manage(actor)

        async with self._uow as uow:
            product = await self._load(uow, command.product_id)
            photos = await uow.media.count_of_kind(product.id, MediaKind.PHOTO)
            ensure_can_be_published(product, photos)

            product.publish(self._clock.now())
            uow.track(product)
            await uow.products.save(product)

        await self._events.publish_all(self._uow.collect_events())


class ChangeProductVisibilityHandler(ProductHandler):
    async def handle(self, command: ChangeProductVisibility, actor: Actor) -> None:
        ensure_can_manage(actor)

        async with self._uow as uow:
            product = await self._load(uow, command.product_id)
            if command.is_visible:
                product.show()
            else:
                product.hide()
            await uow.products.save(product)


class ChangeProductStockHandler(ProductHandler):
    async def handle(self, command: ChangeProductStock, actor: Actor) -> None:
        ensure_can_manage(actor)

        async with self._uow as uow:
            product = await self._load(uow, command.product_id)
            if command.is_in_stock:
                product.restock()
            else:
                product.run_out()
            await uow.products.save(product)


class ChangeMediaLayoutHandler(ProductHandler):
    async def handle(self, command: ChangeMediaLayout, actor: Actor) -> None:
        ensure_can_manage(actor)

        async with self._uow as uow:
            product = await self._load(uow, command.product_id)
            product.show_media_as(command.layout)
            await uow.products.save(product)


class DeleteProductHandler(ProductHandler):
    async def handle(self, command: DeleteProduct, actor: Actor) -> None:
        ensure_can_manage(actor)

        async with self._uow as uow:
            product = await self._load(uow, command.product_id)
            await uow.products.delete(product)
