from uuid import UUID, uuid4

from aiogram.filters.callback_data import CallbackData
import pytest

from telegramsales.shared.presentation.bot.callbacks import (
    PACKED_UUID_LENGTH,
    PackedUUID,
)

MAX_CALLBACK_BYTES = 64


class ProbeCallback(CallbackData, prefix="p"):
    action: str
    first: PackedUUID
    second: PackedUUID


def probe() -> ProbeCallback:
    return ProbeCallback(action="v", first=uuid4(), second=uuid4())


def test_a_packed_id_survives_a_round_trip() -> None:
    original = probe()

    assert ProbeCallback.unpack(original.pack()) == original


def test_an_unpacked_id_is_a_real_uuid() -> None:
    restored = ProbeCallback.unpack(probe().pack())

    assert isinstance(restored.first, UUID)


def test_a_packed_id_is_shorter_than_the_hexadecimal_form() -> None:
    packed = probe().pack().split(":")[2]

    assert len(packed) == PACKED_UUID_LENGTH
    assert len(packed) < len(uuid4().hex)


def test_two_identifiers_fit_into_one_callback() -> None:
    assert len(probe().pack().encode()) <= MAX_CALLBACK_BYTES


def test_a_uuid_passes_through_the_validator_untouched() -> None:
    identifier = uuid4()

    built = ProbeCallback(action="v", first=identifier, second=identifier)

    assert built.first is identifier


@pytest.mark.parametrize(
    "broken",
    [
        "!" * PACKED_UUID_LENGTH,
        "N4TqKJKsSLKKDxtJONK2F",
        "N4TqKJKsSLKKDxtJONK2Fgx",
        "не uuid вовсе",
    ],
)
def test_a_broken_identifier_is_rejected(broken: str) -> None:
    with pytest.raises(ValueError):  # noqa: PT011
        ProbeCallback.unpack(f"p:v:{broken}:{broken}")
