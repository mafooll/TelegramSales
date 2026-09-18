from telegramsales.apps.bot.commands import COMMANDS, bot_commands
from telegramsales.shared.infrastructure.i18n.fluent import FluentTranslations
from telegramsales.shared.settings import LOCALES_PATH

DEFAULT_LOCALE = "ru"
TRANSLATE = FluentTranslations(LOCALES_PATH, DEFAULT_LOCALE)(DEFAULT_LOCALE)

MAX_NAME_LENGTH = 32
MIN_DESCRIPTION_LENGTH = 3
MAX_DESCRIPTION_LENGTH = 256


def test_the_menu_lists_the_commands_the_bot_answers() -> None:
    assert [command.command for command in bot_commands(TRANSLATE)] == [
        "start",
        "shop",
        "find",
        "cart",
        "orders",
        "support",
    ]


def test_every_command_carries_a_translated_description() -> None:
    for command in bot_commands(TRANSLATE):
        assert command.description != ""
        assert not command.description.startswith("menu-")


def test_every_name_fits_the_telegram_rules() -> None:
    for entry in COMMANDS:
        assert entry.name.islower()
        assert len(entry.name) <= MAX_NAME_LENGTH


def test_every_description_fits_the_telegram_limits() -> None:
    for command in bot_commands(TRANSLATE):
        assert len(command.description) >= MIN_DESCRIPTION_LENGTH
        assert len(command.description) <= MAX_DESCRIPTION_LENGTH
