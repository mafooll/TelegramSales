from typing import Protocol

type LocaleCode = str
type TranslationArgs = str | int | float


class ITranslator(Protocol):
    def __call__(self, key: str, /, **args: TranslationArgs) -> str: ...


class ITranslatorFactory(Protocol):
    def __call__(self, locale: LocaleCode | None) -> ITranslator: ...
