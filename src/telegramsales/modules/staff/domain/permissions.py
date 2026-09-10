from enum import StrEnum


class StaffPermission(StrEnum):
    MANAGE_STAFF = "staff.manage"
    VIEW_STAFF = "staff.view"
