from collections.abc import Sequence
from pathlib import Path
from typing import final

from fluent.runtime import FluentLocalization, FluentResourceLoader

from telegramsales.shared.application.i18n import (
    ITranslator,
    LocaleCode,
    TranslationArgs,
)

RESOURCE_SUFFIX = ".ftl"
LOCALE_PLACEHOLDER = "{locale}"


@final
class FluentTranslator:
    def __init__(self, localization: FluentLocalization) -> None:
        self._localization: FluentLocalization = localization

    def __call__(self, key: str, /, **args: TranslationArgs) -> str:
        return self._localization.format_value(key, dict(args))


@final
class FluentTranslations:
    def __init__(self, root: Path, default_locale: LocaleCode) -> None:
        self._default_locale: LocaleCode = default_locale
        self._resource_ids: Sequence[str] = self._discover(root, default_locale)
        self._loader: FluentResourceLoader = FluentResourceLoader(
            str(root / LOCALE_PLACEHOLDER)
        )
        self._cache: dict[LocaleCode, ITranslator] = {}
        self._available: frozenset[LocaleCode] = frozenset(
            entry.name for entry in root.iterdir() if entry.is_dir()
        )

    @staticmethod
    def _discover(root: Path, default_locale: LocaleCode) -> Sequence[str]:
        return sorted(
            path.name for path in (root / default_locale).glob(f"*{RESOURCE_SUFFIX}")
        )

    @property
    def available_locales(self) -> frozenset[LocaleCode]:
        return self._available

    @property
    def resource_ids(self) -> Sequence[str]:
        return self._resource_ids

    def __call__(self, locale: LocaleCode | None) -> ITranslator:
        resolved = locale if locale in self._available else self._default_locale
        if resolved not in self._cache:
            self._cache[resolved] = FluentTranslator(
                FluentLocalization(
                    locales=[resolved, self._default_locale],
                    resource_ids=list(self._resource_ids),
                    resource_loader=self._loader,
                )
            )
        return self._cache[resolved]
