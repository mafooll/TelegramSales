from aiogram import Bot
from aiogram.fsm.storage.base import BaseStorage
import structlog
from structlog.stdlib import BoundLogger
import uvloop

from telegramsales.apps.bot.container import container_context
from telegramsales.apps.bot.desk import subscribe_desk
from telegramsales.apps.bot.dispatcher import build_dispatcher
from telegramsales.apps.bot.notifications import (
    outbox_worker,
    subscribe_notifications,
)
from telegramsales.shared.infrastructure.events.bus import InProcessEventBus
from telegramsales.shared.logger_config import setup_logging
from telegramsales.shared.settings import AppSettings, BotSettings

logger: BoundLogger = structlog.get_logger()


async def run() -> None:
    async with container_context() as container:
        app_settings = await container.get(AppSettings)
        setup_logging(
            log_level=app_settings.log_level,
            use_json=app_settings.log_json,
        )

        bus = await container.get(InProcessEventBus)
        subscribe_desk(bus, container)
        subscribe_notifications(bus, container)

        bot_settings = await container.get(BotSettings)
        bot = await container.get(Bot)
        storage = await container.get(BaseStorage)
        dispatcher = build_dispatcher(container, storage)

        await bot.delete_webhook(
            drop_pending_updates=bot_settings.drop_pending_updates,
        )
        logger.info("bot_starting")
        async with outbox_worker(container):
            await dispatcher.start_polling(bot)  # pyright: ignore[reportUnknownMemberType]


def main() -> None:
    uvloop.run(run())
