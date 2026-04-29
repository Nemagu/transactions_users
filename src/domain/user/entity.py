from domain.entities import Entity
from domain.errors import EntityIdempotentError, EntityPolicyError
from domain.user.value_objects import Email, UserID, UserState, UserStatus
from domain.value_objects import AggregateName, Version


class User(Entity):
    def __init__(
        self,
        user_id: UserID,
        email: Email,
        status: UserStatus,
        state: UserState,
        version: Version,
    ) -> None:
        super().__init__(
            version,
            AggregateName("пользователь"),
            "_user_id",
            "user",
            ["_user_id", "_email", "_status", "_state"],
        )
        self._user_id = user_id
        self._email = email
        self._status = status
        self._state = state

    @property
    def user_id(self) -> UserID:
        return self._user_id

    @property
    def email(self) -> Email:
        return self._email

    @property
    def status(self) -> UserStatus:
        return self._status

    @property
    def state(self) -> UserState:
        return self._state

    def staff(self) -> None:
        self._check_state()
        if self._status == UserStatus.USER:
            raise EntityPolicyError(
                **self._error_data(
                    "пользователь не относится к администрации",
                    {"status": self._status.value},
                )
            )

    def new_email(self, email: Email) -> None:
        self._check_state()
        if self._email == email:
            raise EntityIdempotentError(
                **self._error_data(
                    "новый email идентичен текущему",
                    {"email": self._email.email},
                )
            )
        self._email = email
        self._update_version()

    def appoint_admin(self) -> None:
        if self._status == UserStatus.ADMIN:
            raise EntityIdempotentError(
                **self._error_data(
                    "пользователь уже администратор",
                    {"status": self._status.value},
                )
            )
        self._status = UserStatus.ADMIN
        self._update_version()

    def appoint_user(self) -> None:
        if self._status == UserStatus.USER:
            raise EntityIdempotentError(
                **self._error_data(
                    "пользователь уже не администратор",
                    {"status": self._status.value},
                )
            )
        self._status = UserStatus.USER
        self._update_version()

    def new_state(self, state: UserState) -> None:
        if self._state == state:
            raise EntityIdempotentError(
                **self._error_data(
                    "новое состояние идентично текущему",
                    {"state": self._state.value},
                )
            )
        self._state = state
        self._update_version()

    def activate(self) -> None:
        if self._state.is_active():
            raise EntityIdempotentError(
                **self._error_data(
                    "пользователь уже активный",
                    {"state": self._state.value},
                )
            )
        self._state = UserState.ACTIVE
        self._update_version()

    def freeze(self) -> None:
        if self._state.is_frozen():
            raise EntityIdempotentError(
                **self._error_data(
                    "пользователь уже заморожен",
                    {"state": self._state.value},
                )
            )
        self._state = UserState.FROZEN
        self._update_version()

    def delete(self) -> None:
        if self._state.is_deleted():
            raise EntityIdempotentError(
                **self._error_data(
                    "пользователь уже удален",
                    {"state": self._state.value},
                )
            )
        self._state = UserState.DELETED
        self._update_version()

    def _check_state(self) -> None:
        if self._state.is_frozen():
            raise EntityPolicyError(
                **self._error_data(
                    "пользователь заморожен",
                    {"state": self._state.value},
                )
            )
        if self._state.is_deleted():
            raise EntityPolicyError(
                **self._error_data(
                    "пользователь удален",
                    {"state": self._state.value},
                )
            )
