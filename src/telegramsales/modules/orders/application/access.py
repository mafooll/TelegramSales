from telegramsales.modules.orders.domain.permissions import OrdersPermission
from telegramsales.shared.application.access import Actor, PermissionDeniedError


def ensure_can_manage(actor: Actor) -> None:
    if not actor.can(OrdersPermission.MANAGE_ORDERS):
        raise PermissionDeniedError(
            actor_id=actor.id,
            permission=OrdersPermission.MANAGE_ORDERS,
        )
