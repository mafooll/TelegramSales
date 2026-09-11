from telegramsales.modules.staff.domain.permissions import StaffPermission
from telegramsales.shared.application.access import Actor, PermissionDeniedError


def ensure_can_manage(actor: Actor) -> None:
    if not actor.can(StaffPermission.MANAGE_STAFF):
        raise PermissionDeniedError(
            actor_id=actor.id,
            permission=StaffPermission.MANAGE_STAFF,
        )
