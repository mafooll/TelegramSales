from enum import StrEnum

from telegramsales.shared.application.access import Actor


class AlphaPermission(StrEnum):
    READ = "alpha.read"
    WRITE = "alpha.write"


class BetaPermission(StrEnum):
    READ = "beta.read"


def actor(*permissions: StrEnum) -> Actor:
    return Actor(id=1, permissions=frozenset(p.value for p in permissions))


def test_granted_permission_is_allowed() -> None:
    assert actor(AlphaPermission.READ).can(AlphaPermission.READ)


def test_missing_permission_is_denied() -> None:
    assert not actor(AlphaPermission.READ).can(AlphaPermission.WRITE)


def test_actor_without_permissions_can_do_nothing() -> None:
    assert not actor().can(AlphaPermission.READ)


def test_permissions_of_different_modules_do_not_collide() -> None:
    holder = actor(AlphaPermission.READ)

    assert holder.can(AlphaPermission.READ)
    assert not holder.can(BetaPermission.READ)


def test_an_actor_with_permissions_is_staff() -> None:
    assert actor(AlphaPermission.READ).is_staff


def test_an_actor_without_permissions_is_not_staff() -> None:
    assert not actor().is_staff


def test_actor_context_is_immutable() -> None:
    holder = actor(AlphaPermission.READ)

    assert isinstance(holder.permissions, frozenset)
    assert holder.id == 1
