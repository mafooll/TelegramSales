from datetime import datetime, timedelta
from typing import override

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


class NotificationOutbox(INotificationOutbox):
    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session
        self._models: Repository[NotificationORM, int] = Repository(
            session,
            NotificationORM,
        )

    @override
    async def next_id(self) -> NotificationId:
        sequence = func.pg_get_serial_sequence(
            NotificationORM.__tablename__,
            ID_COLUMN,
        )
        issued = (
            await self._session.execute(select(func.nextval(sequence)))
        ).scalar_one()
        return NotificationId(issued)

    @override
    async def add(self, notification: Notification) -> bool:
        model = notification_to_model(notification)
        statement = (
            insert(NotificationORM)
            .values(
                id=model.id,
                recipient_id=model.recipient_id,
                key=model.key,
                args=model.args,
                dedup_key=model.dedup_key,
                status=model.status,
                attempts=model.attempts,
                available_at=model.available_at,
                created_at=model.created_at,
                reason=model.reason,
            )
            .on_conflict_do_nothing(index_elements=[DEDUP_COLUMN])
            .returning(NotificationORM.id)
        )
        queued = (await self._session.execute(statement)).scalar_one_or_none()
        await self._session.flush()
        return queued is not None

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
