from telegramsales.modules.catalog.domain.permissions import CatalogPermission
from telegramsales.shared.application.access import Actor, PermissionDeniedError


def ensure_can_manage(actor: Actor) -> None:
    if not actor.can(CatalogPermission.MANAGE):
        raise PermissionDeniedError(
            actor_id=actor.id,
            permission=CatalogPermission.MANAGE,
        )
