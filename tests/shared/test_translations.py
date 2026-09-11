from collections.abc import Iterator
import importlib
from pathlib import Path

from fluent.syntax import FluentParser, ast as ftl
import pytest

import telegramsales
from telegramsales.shared.infrastructure.i18n.fluent import FluentTranslations
from telegramsales.shared.presentation.bot import texts
from telegramsales.shared.settings import LOCALES_PATH

DEFAULT_LOCALE = "ru"
PACKAGE_ROOT = Path(telegramsales.__file__).resolve().parent


def declared_keys() -> set[str]:
    keys: set[str] = set()
    for path in sorted(PACKAGE_ROOT.rglob("*texts.py")):
        relative = path.relative_to(PACKAGE_ROOT.parent).with_suffix("")
        module = importlib.import_module(".".join(relative.parts))
        keys.update(
            value
            for name, value in vars(module).items()
            if name.isupper() and isinstance(value, str)
        )
    return keys


def defined_keys(locale: str) -> set[str]:
    parser = FluentParser()
    return {
        entry.id.name
        for path in (LOCALES_PATH / locale).glob("*.ftl")
        for entry in parser.parse(path.read_text(encoding="utf-8")).body
        if isinstance(entry, ftl.Message)
    }


def available_locales() -> Iterator[str]:
    yield from sorted(
        entry.name for entry in LOCALES_PATH.iterdir() if entry.is_dir()
    )


@pytest.fixture
def translations() -> FluentTranslations:
    return FluentTranslations(LOCALES_PATH, DEFAULT_LOCALE)


@pytest.mark.parametrize("locale", list(available_locales()))
def test_every_declared_key_is_translated(locale: str) -> None:
    assert declared_keys() - defined_keys(locale) == set()


@pytest.mark.parametrize("locale", list(available_locales()))
def test_no_translation_is_orphaned(locale: str) -> None:
    assert defined_keys(locale) - declared_keys() == set()


def test_a_key_resolves_to_its_translation(translations: FluentTranslations) -> None:
    assert translations(DEFAULT_LOCALE)(texts.HOME) == "⬅️ В меню"


def test_arguments_are_interpolated(translations: FluentTranslations) -> None:
    translate = translations(DEFAULT_LOCALE)

    assert translate(texts.PAGE_POSITION, current=1, total=3) == "1/3"


def test_unknown_locale_falls_back_to_the_default(
    translations: FluentTranslations,
) -> None:
    assert translations("xx")(texts.HOME) == translations(DEFAULT_LOCALE)(texts.HOME)


def test_missing_locale_is_not_reported_as_available(
    translations: FluentTranslations,
) -> None:
    assert "xx" not in translations.available_locales
