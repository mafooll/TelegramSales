from typing import Any


class BaseError(Exception):
    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message: str = message
        self.details: dict[str, Any] = details or {}

    def to_dict(self) -> dict[str, Any]:
        return {"message": self.message, "details": self.details}


class DomainError(BaseError):
    pass


class ApplicationError(BaseError):
    pass


class InfrastructureError(BaseError):
    pass
