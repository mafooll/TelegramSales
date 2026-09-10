from dataclasses import dataclass

from telegramsales.shared.application.access import Actor
from telegramsales.shared.application.i18n import ITranslator


@dataclass(frozen=True, slots=True)
class RenderContext:
    actor: Actor
    translate: ITranslator
