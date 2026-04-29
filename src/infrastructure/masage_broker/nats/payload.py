from pydantic import BaseModel

from application.dto.user import UserVersionSimpleDTO
from application.ports.event_publisher import PublishEventDTO


class UserPayload(BaseModel):
    user_id: str
    email: str
    status: str
    state: str
    version: int
    event: str
    editor_id: str | None
    created_at: str

    @classmethod
    def from_dto(cls, dto: PublishEventDTO) -> "UserPayload":
        model = UserVersionSimpleDTO.from_dto(dto)
        return cls(
            user_id=str(model.user_id),
            email=model.email,
            status=model.status,
            state=model.state,
            version=model.version,
            event=model.event,
            editor_id=str(model.editor_id) if model.editor_id is not None else None,
            created_at=model.created_at.isoformat(),
        )
