from aiogram.types import (
    InputRichBlockCollage,
    InputRichBlockParagraph,
    InputRichBlockPhoto,
    InputRichBlockSlideshow,
    InputRichBlockVideo,
)

from telegramsales.shared.presentation.bot.content import (
    content_blocks,
    gallery,
    paragraph,
    photo,
    slideshow,
    video,
)

FIRST = "AgACAgIAAxkBAAI-first"
SECOND = "AgACAgIAAxkBAAI-second"
CLIP = "BAACAgIAAxkBAAI-clip"


def test_a_string_becomes_a_single_paragraph() -> None:
    blocks = content_blocks("Заголовок")

    assert len(blocks) == 1
    assert isinstance(blocks[0], InputRichBlockParagraph)
    assert blocks[0].text == "Заголовок"


def test_prepared_blocks_pass_through_unchanged() -> None:
    prepared = [paragraph("Товар"), photo(FIRST)]

    assert content_blocks(prepared) == prepared


def test_a_photo_carries_its_file_id() -> None:
    block = photo(FIRST)

    assert isinstance(block, InputRichBlockPhoto)
    assert block.photo.media == FIRST


def test_a_photo_may_carry_a_caption() -> None:
    block = photo(FIRST, "Вид спереди")

    assert isinstance(block, InputRichBlockPhoto)
    assert block.caption is not None
    assert block.caption.text == "Вид спереди"


def test_a_video_carries_its_file_id() -> None:
    block = video(CLIP)

    assert isinstance(block, InputRichBlockVideo)
    assert block.video.media == CLIP


def test_no_images_render_nothing() -> None:
    assert gallery([]) == []


def test_a_single_image_renders_as_a_plain_photo() -> None:
    blocks = gallery([FIRST], "Подпись")

    assert len(blocks) == 1
    assert isinstance(blocks[0], InputRichBlockPhoto)
    assert blocks[0].caption is not None
    assert blocks[0].caption.text == "Подпись"


def test_several_images_render_as_one_collage() -> None:
    blocks = gallery([FIRST, SECOND])

    assert len(blocks) == 1
    collage = blocks[0]
    assert isinstance(collage, InputRichBlockCollage)
    assert len(collage.blocks) == 2
    assert [
        inner.photo.media
        for inner in collage.blocks
        if isinstance(inner, InputRichBlockPhoto)
    ] == [FIRST, SECOND]


def test_a_slideshow_groups_the_same_way() -> None:
    blocks = slideshow([FIRST, SECOND])

    assert isinstance(blocks[0], InputRichBlockSlideshow)


def test_a_slideshow_of_one_is_still_a_plain_photo() -> None:
    assert isinstance(slideshow([FIRST])[0], InputRichBlockPhoto)
