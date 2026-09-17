from telegramsales.modules.desk.contracts import ThreadId
from telegramsales.shared.domain.exceptions import InfrastructureError


class TopicGoneError(InfrastructureError):
    def __init__(self, *, thread_id: ThreadId | None) -> None:
        super().__init__(
            f"topic {thread_id} no longer exists",
            details={"thread_id": thread_id},
        )
