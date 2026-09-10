from datetime import UTC, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from telegramsales.modules.staff.contracts import StaffId
from telegramsales.modules.staff.domain.entities import StaffMember
from telegramsales.modules.staff.domain.enums import StaffRole
from telegramsales.modules.staff.infrastructure.queries import StaffQueries
from telegramsales.modules.staff.infrastructure.repositories import StaffRepository
from telegramsales.modules.staff.infrastructure.uow import StaffUnitOfWork
from telegramsales.shared.infrastructure.database.uow import SessionFactory
from tests.staff.factories import MEMBER, NOW, OTHER, OWNER, make_member

pytestmark = pytest.mark.db


async def store(session: AsyncSession, *members: StaffMember) -> StaffRepository:
    repository = StaffRepository(session)
    for member in members:
        await repository.add(member)
    return repository


async def test_member_survives_a_round_trip(session: AsyncSession) -> None:
    repository = await store(session, make_member(StaffRole.OWNER))

    loaded = await repository.get(MEMBER)

    assert loaded is not None
    assert loaded.id == MEMBER
    assert loaded.role is StaffRole.OWNER
    assert loaded.is_active
    assert loaded.created_at == NOW


async def test_loading_registers_no_events(session: AsyncSession) -> None:
    repository = await store(session, make_member(StaffRole.MANAGER))

    loaded = await repository.get(MEMBER)

    assert loaded is not None
    assert loaded.collect_events() == []


async def test_timestamp_keeps_its_timezone(session: AsyncSession) -> None:
    repository = await store(session, make_member(StaffRole.MANAGER))

    loaded = await repository.get(MEMBER)

    assert loaded is not None
    assert loaded.created_at.tzinfo is not None
    assert loaded.created_at.astimezone(UTC) == NOW


async def test_save_does_not_clobber_untouched_columns(
    session: AsyncSession,
) -> None:
    repository = await store(session, make_member(StaffRole.MANAGER))
    member = await repository.get(MEMBER)
    assert member is not None

    member.change_role(StaffRole.OWNER, changed_by=OWNER)
    await repository.save(member)

    reloaded = await repository.get(MEMBER)
    assert reloaded is not None
    assert reloaded.role is StaffRole.OWNER
    assert reloaded.created_at == NOW


async def test_revoked_members_are_not_counted(session: AsyncSession) -> None:
    revoked = make_member(StaffRole.OWNER, staff_id=OWNER)
    revoked.is_active = False
    repository = await store(
        session,
        make_member(StaffRole.OWNER, staff_id=MEMBER),
        revoked,
    )

    assert await repository.count_active_by_role(StaffRole.OWNER) == 1


async def test_unknown_member_is_none(session: AsyncSession) -> None:
    repository = StaffRepository(session)

    assert await repository.get(StaffId(999)) is None


async def test_queries_return_views_not_entities(session: AsyncSession) -> None:
    await store(session, make_member(StaffRole.OWNER))
    await session.flush()

    view = await StaffQueries(session).get(MEMBER)

    assert view is not None
    assert view.id == MEMBER
    assert view.role is StaffRole.OWNER
    assert view.is_active
    assert not hasattr(view, "collect_events")


async def test_list_page_returns_every_member(session: AsyncSession) -> None:
    await store(
        session,
        make_member(StaffRole.OWNER, staff_id=OWNER),
        make_member(StaffRole.MANAGER, staff_id=OTHER),
    )
    await session.flush()

    page = await StaffQueries(session).list_page(0, 10)

    assert {view.id for view in page.items} == {OWNER, OTHER}
    assert page.total == 2
    assert page.is_single


async def test_list_page_slices_and_reports_the_total(session: AsyncSession) -> None:
    await store(
        session,
        make_member(StaffRole.OWNER, staff_id=OWNER),
        make_member(StaffRole.MANAGER, staff_id=OTHER),
        make_member(StaffRole.MANAGER, staff_id=MEMBER),
    )
    await session.flush()

    first = await StaffQueries(session).list_page(0, 2)
    second = await StaffQueries(session).list_page(1, 2)

    assert len(first.items) == 2
    assert len(second.items) == 1
    assert first.total == second.total == 3
    assert first.has_next
    assert not second.has_next


async def test_unit_of_work_collects_events_after_commit(
    session_factory: SessionFactory,
) -> None:
    uow = StaffUnitOfWork(session_factory)

    async with uow:
        member = StaffMember.create(
            staff_id=MEMBER,
            role=StaffRole.MANAGER,
            created_by=OWNER,
            now=datetime.now(UTC),
        )
        await uow.staff.add(member)
        uow.track(member)

    events = uow.collect_events()
    assert len(events) == 1
    assert events[0].event_type == "StaffMemberCreated"


async def test_unknown_role_is_rejected_by_the_database(
    session: AsyncSession,
) -> None:

    statement = text("""
        insert into staff_members (id, role, is_active, created_at)
        values (1, 'wizard', true, now())
    """)

    with pytest.raises(IntegrityError, match="known_role"):
        await session.execute(statement)
