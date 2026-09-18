from dataclasses import dataclass

from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats

from telegramsales.apps.bot import texts
from telegramsales.modules.catalog import FIND_COMMAND, SHOP_COMMAND
from telegramsales.modules.desk import SUPPORT_COMMAND
from telegramsales.modules.orders import CART_COMMAND, ORDERS_COMMAND
from telegramsales.shared.application.i18n import ITranslator

START_COMMAND = "start"


@dataclass(frozen=True, slots=True)
class CommandEntry:
    name: str
    description_key: str


COMMANDS: tuple[CommandEntry, ...] = (
    CommandEntry(name=START_COMMAND, description_key=texts.START_DESCRIPTION),
    CommandEntry(name=SHOP_COMMAND, description_key=texts.SHOP_DESCRIPTION),
    CommandEntry(name=FIND_COMMAND, description_key=texts.FIND_DESCRIPTION),
    CommandEntry(name=CART_COMMAND, description_key=texts.CART_DESCRIPTION),
    CommandEntry(name=ORDERS_COMMAND, description_key=texts.ORDERS_DESCRIPTION),
    CommandEntry(name=SUPPORT_COMMAND, description_key=texts.SUPPORT_DESCRIPTION),
)


def bot_commands(translate: ITranslator) -> list[BotCommand]:
    return [
        BotCommand(
            command=entry.name,
            description=translate(entry.description_key),
        )
        for entry in COMMANDS
    ]


async def publish_commands(bot: Bot, translate: ITranslator) -> None:
    await bot.set_my_commands(
        commands=bot_commands(translate),
        scope=BotCommandScopeAllPrivateChats(),
    )
