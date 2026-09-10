import base64
from typing import Annotated
from uuid import UUID

from pydantic import BeforeValidator, PlainSerializer

PACKED_UUID_LENGTH = 22
_BASE64_ALT_CHARS = b"-_"
_BASE64_PADDING = "=="


def _pack_uuid(value: UUID) -> str:
    return base64.urlsafe_b64encode(value.bytes).rstrip(b"=").decode()


def _unpack_uuid(value: object) -> object:
    if not isinstance(value, str) or len(value) != PACKED_UUID_LENGTH:
        return value
    return UUID(
        bytes=base64.b64decode(
            value + _BASE64_PADDING,
            altchars=_BASE64_ALT_CHARS,
            validate=True,
        )
    )


PackedUUID = Annotated[
    UUID,
    BeforeValidator(_unpack_uuid),
    PlainSerializer(_pack_uuid, return_type=str),
]
