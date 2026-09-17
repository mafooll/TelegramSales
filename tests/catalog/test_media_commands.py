import pytest

from telegramsales.modules.catalog.application.commands.media import (
    AttachMedia,
    AttachMediaHandler,
    DetachMedia,
    DetachMediaHandler,
)
from telegramsales.modules.catalog.application.exceptions import (
    MediaNotFoundError,
    ProductNotFoundError,
)
from telegramsales.modules.catalog.contracts import MediaId, ProductId
from telegramsales.modules.catalog.domain.entities import ProductMedia
from telegramsales.modules.catalog.domain.enums import MediaKind
from telegramsales.modules.catalog.domain.exceptions import (
    TooManyPhotosError,
    TooManyVideosError,
)
from telegramsales.modules.catalog.domain.permissions import CatalogPermission
from telegramsales.modules.catalog.domain.services import MAX_PHOTOS
from telegramsales.shared.application.access import PermissionDeniedError
from tests.catalog.factories import (
    COAT,
    DRESS,
    FRONT_PHOTO,
    make_media,
    make_product,
)
from tests.catalog.fakes import (
    FakeCatalogUnitOfWork,
    FakeProductMediaRepository,
    FakeProductRepository,
    actor_with,
)

MANAGER = actor_with(CatalogPermission.MANAGE)
OUTSIDER = actor_with()


def uow_with(*media: ProductMedia) -> FakeCatalogUnitOfWork:
    return FakeCatalogUnitOfWork(
        products=FakeProductRepository(make_product()),
        media=FakeProductMediaRepository(*media),
    )


def photo(index: int) -> ProductMedia:
    return make_media(MediaId(600 + index), file_id=f"photo-{index}")


async def test_photo_is_attached() -> None:
    uow = uow_with()

    media_id = await AttachMediaHandler(uow).handle(
        AttachMedia(product_id=COAT, kind=MediaKind.PHOTO, file_id="front"),
        MANAGER,
    )

    assert uow.media.items[media_id].file_id == "front"


async def test_attached_photos_keep_their_order() -> None:
    uow = uow_with()
    handler = AttachMediaHandler(uow)

    first = await handler.handle(
        AttachMedia(product_id=COAT, kind=MediaKind.PHOTO, file_id="one"), MANAGER
    )
    second = await handler.handle(
        AttachMedia(product_id=COAT, kind=MediaKind.PHOTO, file_id="two"), MANAGER
    )

    assert uow.media.items[first].position < uow.media.items[second].position


async def test_the_photo_above_the_limit_is_rejected() -> None:
    uow = uow_with(*[photo(index) for index in range(MAX_PHOTOS)])

    with pytest.raises(TooManyPhotosError):
        await AttachMediaHandler(uow).handle(
            AttachMedia(product_id=COAT, kind=MediaKind.PHOTO, file_id="extra"),
            MANAGER,
        )


async def test_the_second_video_is_rejected() -> None:
    uow = uow_with(make_media(MediaId(700), MediaKind.VIDEO, file_id="clip"))

    with pytest.raises(TooManyVideosError):
        await AttachMediaHandler(uow).handle(
            AttachMedia(product_id=COAT, kind=MediaKind.VIDEO, file_id="another"),
            MANAGER,
        )


async def test_a_video_does_not_count_against_photos() -> None:
    uow = uow_with(*[photo(index) for index in range(MAX_PHOTOS)])

    media_id = await AttachMediaHandler(uow).handle(
        AttachMedia(product_id=COAT, kind=MediaKind.VIDEO, file_id="clip"), MANAGER
    )

    assert uow.media.items[media_id].kind is MediaKind.VIDEO


async def test_attaching_to_a_missing_product_is_rejected() -> None:
    uow = uow_with()

    with pytest.raises(ProductNotFoundError):
        await AttachMediaHandler(uow).handle(
            AttachMedia(
                product_id=ProductId(DRESS), kind=MediaKind.PHOTO, file_id="x"
            ),
            MANAGER,
        )


async def test_outsider_cannot_attach_media() -> None:
    uow = uow_with()

    with pytest.raises(PermissionDeniedError):
        await AttachMediaHandler(uow).handle(
            AttachMedia(product_id=COAT, kind=MediaKind.PHOTO, file_id="front"),
            OUTSIDER,
        )


async def test_media_is_detached() -> None:
    uow = uow_with(make_media())

    await DetachMediaHandler(uow).handle(DetachMedia(media_id=FRONT_PHOTO), MANAGER)

    assert FRONT_PHOTO not in uow.media.items


async def test_detaching_missing_media_is_rejected() -> None:
    uow = uow_with()

    with pytest.raises(MediaNotFoundError):
        await DetachMediaHandler(uow).handle(
            DetachMedia(media_id=MediaId(404)), MANAGER
        )
