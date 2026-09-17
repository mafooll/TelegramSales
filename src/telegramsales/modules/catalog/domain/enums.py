from enum import StrEnum


class MediaKind(StrEnum):
    PHOTO = "photo"
    VIDEO = "video"


class MediaLayout(StrEnum):
    COLLAGE = "collage"
    SLIDESHOW = "slideshow"
