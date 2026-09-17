from dataclasses import dataclass

from telegramsales.modules.catalog.application.access import ensure_can_manage
from telegramsales.modules.catalog.application.exceptions import (
    MediaNotFoundError,
    ProductNotFoundError,
)
from telegramsales.modules.catalog.application.ports import ICatalogUnitOfWork
from telegramsales.modules.catalog.contracts import MediaId, ProductId
from telegramsales.modules.catalog.domain.entities import ProductMedia
from telegramsales.modules.catalog.domain.enums import MediaKind
from telegramsales.modules.catalog.domain.services import (
    ensure_photo_fits,
    ensure_video_fits,
)
from telegramsales.shared.application.access import Actor

NEXT_POSITION = 1


@dataclass(frozen=True, slots=True)
class AttachMedia:
    product_id: ProductId
    kind: MediaKind
    file_id: str


@dataclass(frozen=True, slots=True)
class DetachMedia:
    media_id: MediaId


class AttachMediaHandler:
    def __init__(self, uow: ICatalogUnitOfWork) -> None:
        self._uow: ICatalogUnitOfWork = uow

    async def handle(self, command: AttachMedia, actor: Actor) -> MediaId:
        ensure_can_manage(actor)

        async with self._uow as uow:
            if not await uow.products.get(command.product_id):
                raise ProductNotFoundError(product_id=command.product_id)

            taken = await uow.media.count_of_kind(command.product_id, command.kind)
            if command.kind is MediaKind.PHOTO:
                ensure_photo_fits(taken)
            else:
                ensure_video_fits(taken)

            media = ProductMedia.create(
                media_id=await uow.media.next_id(),
                product_id=command.product_id,
                kind=command.kind,
                file_id=command.file_id,
                position=taken + NEXT_POSITION,
            )
            await uow.media.add(media)

        return media.id


class DetachMediaHandler:
    def __init__(self, uow: ICatalogUnitOfWork) -> None:
        self._uow: ICatalogUnitOfWork = uow

    async def handle(self, command: DetachMedia, actor: Actor) -> None:
        ensure_can_manage(actor)

        async with self._uow as uow:
            media = await uow.media.get(command.media_id)
            if media is None:
                raise MediaNotFoundError(media_id=command.media_id)
            await uow.media.delete(media)
