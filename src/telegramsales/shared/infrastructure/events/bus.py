from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any, override

import structlog
from structlog.stdlib import BoundLogger

from telegramsales.shared.application.events import IEventPublisher
from telegramsales.shared.domain.event import DomainEvent

logger: BoundLogger = structlog.get_logger()

type EventHandler[EventType: DomainEvent] = Callable[[EventType], Awaitable[None]]
type HandlerRegistry = dict[type[DomainEvent], list[EventHandler[Any]]]


class InProcessEventBus(IEventPublisher):
    def __init__(self) -> None:
        self._handlers: HandlerRegistry = defaultdict(list)

    def subscribe[EventType: DomainEvent](
        self,
        event_type: type[EventType],
        handler: EventHandler[EventType],
    ) -> None:
        self._handlers[event_type].append(handler)

    async def publish(self, event: DomainEvent) -> None:
        for handler in self._handlers.get(type(event), []):
            try:
                await handler(event)
            except Exception:
                logger.warning(
                    "event_handler_failed",
                    event_type=event.event_type,
                    event_id=str(event.event_id),
                    handler=getattr(handler, "__qualname__", repr(handler)),
                    exc_info=True,
                )

    @override
    async def publish_all(self, events: list[DomainEvent]) -> None:
        for event in events:
            await self.publish(event)
