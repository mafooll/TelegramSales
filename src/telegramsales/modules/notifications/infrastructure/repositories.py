from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Any, override

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from telegramsales.modules.notifications.application.ports import (
    INotificationOutbox,
    ISubscriptionRepository,
)
from telegramsales.modules.notifications.contracts import (
    NotificationId,
    RecipientId,
)
from telegramsales.modules.notifications.domain.entities import (
    Notification,
    Subscription,
)
from telegramsales.modules.notifications.domain.enums import NotificationStatus
from telegramsales.modules.notifications.infrastructure.mappers import (
    notification_to_entity,
    notification_to_model,
    subscription_to_entity,
    subscription_to_model,
)
from telegramsales.modules.notifications.infrastructure.models import (
    NotificationORM,
    SubscriptionORM,
)
from telegramsales.shared.infrastructure.database.repository import Repository

ID_COLUMN = "id"
DEDUP_COLUMN = "dedup_key"
LEASE = timedelta(seconds=60)
SINGLE = 1


def _row_of(notification: Notification) -> dict[str, Any]:
    model = notification_to_model(notification)
    return {
        "id": model.id,
        "recipient_id": model.recipient_id,
        "key": model.key,
        "args": model.args,
        "action_key": model.action_key,
        "action_data": model.action_data,
        "dedup_key": model.dedup_key,
        "status": model.status,
        "attempts": model.attempts,
        "available_at": model.available_at,
        "created_at": model.created_at,
        "reason": model.reason,
    }


class NotificationOutbox(INotificationOutbox):
    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session
        self._models: Repository[NotificationORM, int] = Repository(
            session,
            NotificationORM,
        )

    @override
    async def next_id(self) -> NotificationId:
        issued = await self.next_ids(SINGLE)
        return issued[0]

    @override
    async def next_ids(self, count: int) -> list[NotificationId]:
        if count < SINGLE:
            return []

        sequence = func.pg_get_serial_sequence(
            NotificationORM.__tablename__,
            ID_COLUMN,
        )
        query = select(func.nextval(sequence)).select_from(
            func.generate_series(SINGLE, count)
        )
        issued = (await self._session.execute(query)).scalars().all()
        return [NotificationId(value) for value in issued]

    @override
    async def add(self, notification: Notification) -> bool:
        return await self.add_all([notification]) == SINGLE

    @override
    async def add_all(self, notifications: Sequence[Notification]) -> int:
        if not notifications:
            return 0

        statement = (
            insert(NotificationORM)
            .values([_row_of(notification) for notification in notifications])
            .on_conflict_do_nothing(index_elements=[DEDUP_COLUMN])
            .returning(NotificationORM.id)
        )
        queued = (await self._session.execute(statement)).scalars().all()
        await self._session.flush()
        return len(queued)

    @override
    async def claim(self, limit: int, now: datetime) -> list[Notification]:
        due = (
            select(NotificationORM.id)
            .where(
                NotificationORM.status == NotificationStatus.PENDING.value,
                NotificationORM.available_at <= now,
            )
            .order_by(NotificationORM.available_at, NotificationORM.id)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        leased = (
            update(NotificationORM)
            .where(NotificationORM.id.in_(due.scalar_subquery()))
            .values(available_at=now + LEASE)
            .returning(NotificationORM)
        )
        models = (await self._session.execute(leased)).scalars().all()
        await self._session.flush()
        return [notification_to_entity(model) for model in models]

    @override
    async def save(self, notification: Notification) -> None:
        await self._models.merge(notification_to_model(notification))


class SubscriptionRepository(ISubscriptionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session
        self._models: Repository[SubscriptionORM, int] = Repository(
            session,
            SubscriptionORM,
        )

    @override
    async def get(self, recipient_id: RecipientId) -> Subscription | None:
        model = await self._models.get(recipient_id)
        return subscription_to_entity(model) if model is not None else None

    @override
    async def add(self, subscription: Subscription) -> None:
        await self._models.add(subscription_to_model(subscription))

    @override
    async def save(self, subscription: Subscription) -> None:
        await self._models.merge(subscription_to_model(subscription))

    @override
    async def recipients(self) -> list[RecipientId]:
        query = (
            select(SubscriptionORM.id)
            .where(SubscriptionORM.is_on.is_(True))
            .order_by(SubscriptionORM.id)
        )
        rows = (await self._session.execute(query)).scalars().all()
        return [RecipientId(row) for row in rows]
