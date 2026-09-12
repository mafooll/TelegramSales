from typing import NewType
from uuid import UUID

CartItemId = NewType("CartItemId", int)
OrderId = NewType("OrderId", UUID)
SelectionId = NewType("SelectionId", UUID)
