from typing import Self
from uuid import UUID

from pydantic import BaseModel

from application.command.public.user import (
    AuthCodeSendingCommand,
    CodeAuthCommand,
    NewEmailConfirmingCommand,
    PasswordAuthCommand,
    UserConfirmingEmailCommand,
    UserCreatingCommand,
    UserEmailChangingCommand,
)
from application.dto.user import UserSimpleDTO


class UserSimpleResponse(BaseModel):
    user_id: UUID
    email: str
    status: str
    state: str
    version: int

    @classmethod
    def from_dto(cls, dto: UserSimpleDTO) -> Self:
        return cls(
            user_id=dto.user_id,
            email=dto.email,
            status=dto.status,
            state=dto.state,
            version=dto.version,
        )


class UserConfirmEmailRequest(BaseModel):
    email: str

    def to_command(self) -> UserConfirmingEmailCommand:
        return UserConfirmingEmailCommand(email=self.email)


class UserCreateRequest(BaseModel):
    email: str
    code: int
    password: str

    def to_command(self) -> UserCreatingCommand:
        return UserCreatingCommand(email=self.email, code=self.code, password=self.password)


class AuthCodeSendRequest(BaseModel):
    email: str

    def to_command(self) -> AuthCodeSendingCommand:
        return AuthCodeSendingCommand(email=self.email)


class AuthCodeRequest(BaseModel):
    email: str
    code: int

    def to_command(self) -> CodeAuthCommand:
        return CodeAuthCommand(email=self.email, code=self.code)


class AuthPasswordRequest(BaseModel):
    email: str
    password: str

    def to_command(self) -> PasswordAuthCommand:
        return PasswordAuthCommand(email=self.email, password=self.password)


class ConfirmNewEmailRequest(BaseModel):
    new_email: str

    def to_command(self, initiator_id: UUID) -> NewEmailConfirmingCommand:
        return NewEmailConfirmingCommand(initiator_id=initiator_id, new_email=self.new_email)


class ChangeEmailRequest(BaseModel):
    new_email: str
    new_email_code: int
    old_email_code: int

    def to_command(self, initiator_id: UUID) -> UserEmailChangingCommand:
        return UserEmailChangingCommand(
            initiator_id=initiator_id,
            new_email=self.new_email,
            new_email_code=self.new_email_code,
            old_email_code=self.old_email_code,
        )
