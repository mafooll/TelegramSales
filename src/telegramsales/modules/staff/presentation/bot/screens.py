from telegramsales.modules.staff.application.queries import StaffMemberView
from telegramsales.modules.staff.presentation.bot import texts
from telegramsales.modules.staff.presentation.bot.buttons import (
    BACK_TO_LIST,
    GRANT_ACCESS,
    MAKE_MANAGER,
    MAKE_OWNER,
    MEMBER_ENTRY,
    RESTORE_ACCESS,
    REVOKE_ACCESS,
)
from telegramsales.modules.staff.presentation.bot.views import (
    StaffListView,
    role_key,
)
from telegramsales.shared.presentation.bot.keyboard import ListScreen, Screen
from telegramsales.shared.presentation.bot.navigation import home_button

STAFF_LIST: ListScreen[StaffMemberView, StaffListView] = ListScreen(
    content=lambda view, translate: translate(
        texts.STAFF_LIST_EMPTY if view.total == 0 else texts.STAFF_LIST,
        total=view.total,
    ),
    item=MEMBER_ENTRY,
    footer=[GRANT_ACCESS, home_button()],
)

MEMBER_CARD: Screen[StaffMemberView] = Screen(
    content=lambda member, translate: translate(
        texts.MEMBER_CARD,
        id=str(member.id),
        role=translate(role_key(member)),
    ),
    buttons=[MAKE_OWNER, MAKE_MANAGER, RESTORE_ACCESS, REVOKE_ACCESS, BACK_TO_LIST],
)
