from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.shared.domain.exceptions import DomainError


class CustomerBlockedError(DomainError):
    def __init__(self, *, customer_id: CustomerId) -> None:
        super().__init__(
            f"customer {customer_id} is blocked",
            details={"customer_id": customer_id},
        )
