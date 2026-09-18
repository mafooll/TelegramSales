from collections.abc import Sequence

from aiogram.types import (
    InputMediaPhoto,
    InputMediaVideo,
    InputRichBlockCollage,
    InputRichBlockDivider,
    InputRichBlockFooter,
    InputRichBlockParagraph,
    InputRichBlockPhoto,
    InputRichBlockSectionHeading,
    InputRichBlockSlideshow,
    InputRichBlockUnion,
    InputRichBlockVideo,
    InputRichMessage,
    RichBlockCaption,
    RichTextBold,
    RichTextCode,
    RichTextUnion,
)

type Content = str | Sequence[InputRichBlockUnion]

SINGLE_ITEM = 1
HEADING_SIZE = 2
MEDIA_BLOCKS = (
    InputRichBlockPhoto,
    InputRichBlockVideo,
    InputRichBlockCollage,
    InputRichBlockSlideshow,
)


def _caption(text: str | None) -> RichBlockCaption | None:
    return None if text is None else RichBlockCaption(text=text)


def paragraph(text: str) -> InputRichBlockUnion:
    return InputRichBlockParagraph(text=text)


def code(text: str) -> RichTextCode:
    return RichTextCode(text=text)


def bold(text: str) -> RichTextBold:
    return RichTextBold(text=text)


def heading(text: str, size: int = HEADING_SIZE) -> InputRichBlockUnion:
    return InputRichBlockSectionHeading(text=text, size=size)


def parts(*pieces: str | RichTextUnion) -> InputRichBlockUnion:
    return InputRichBlockParagraph(text=list(pieces))


def divider() -> InputRichBlockUnion:
    return InputRichBlockDivider()


def footnote(text: str) -> InputRichBlockUnion:
    return InputRichBlockFooter(text=text)


def photo(file_id: str, caption: str | None = None) -> InputRichBlockUnion:
    return InputRichBlockPhoto(
        photo=InputMediaPhoto(media=file_id),
        caption=_caption(caption),
    )


def video(file_id: str, caption: str | None = None) -> InputRichBlockUnion:
    return InputRichBlockVideo(
        video=InputMediaVideo(media=file_id),
        caption=_caption(caption),
    )


def gallery(
    file_ids: Sequence[str],
    caption: str | None = None,
) -> list[InputRichBlockUnion]:
    if not file_ids:
        return []
    if len(file_ids) == SINGLE_ITEM:
        return [photo(file_ids[0], caption)]
    return [
        InputRichBlockCollage(
            blocks=[photo(file_id) for file_id in file_ids],
            caption=_caption(caption),
        )
    ]


def slideshow(
    file_ids: Sequence[str],
    caption: str | None = None,
) -> list[InputRichBlockUnion]:
    if not file_ids:
        return []
    if len(file_ids) == SINGLE_ITEM:
        return [photo(file_ids[0], caption)]
    return [
        InputRichBlockSlideshow(
            blocks=[photo(file_id) for file_id in file_ids],
            caption=_caption(caption),
        )
    ]


def content_blocks(content: Content) -> list[InputRichBlockUnion]:
    if isinstance(content, str):
        return [paragraph(content)]
    return list(content)


def without_media(message: InputRichMessage) -> InputRichMessage:
    blocks: list[InputRichBlockUnion] = []
    for block in message.blocks or []:
        if not isinstance(block, MEDIA_BLOCKS):
            blocks.append(block)
            continue
        if block.caption is not None:
            blocks.append(paragraph(str(block.caption.text)))
    return InputRichMessage(blocks=blocks)
