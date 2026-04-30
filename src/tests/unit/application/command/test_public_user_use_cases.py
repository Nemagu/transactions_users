from datetime import timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest

from application.command.private.user import UserPublicationUseCase
from application.command.public.user import (
    AuthCodeSendingCommand,
    AuthCodeSendingUseCase,
    CodeAuthCommand,
    CodeAuthUseCase,
    NewEmailConfirmingCommand,
    NewEmailConfirmingUseCase,
    UserAppointingAdminCommand,
    UserAppointingAdminUseCase,
    UserAppointingUserCommand,
    UserAppointingUserUseCase,
    UserConfirmingEmailCommand,
    UserConfirmingEmailUseCase,
    UserCreatingCommand,
    UserCreatingUseCase,
    UserEmailChangingCommand,
    UserEmailChangingUseCase,
    UserFreezingCommand,
    UserFreezingUseCase,
)
from application.errors import AppInvalidDataError, AppNotFoundError
from application.ports.repositories import UserEvent
from domain.user.value_objects import UserStatus


class _FakeUow:
    def __init__(self, *, by_email=None, by_id=None, next_id=None):
        self._by_email = by_email
        self._by_id = by_id
        self._next_id = next_id
        self.saved_users = []
        self.version_saved = []
        self.saved_passwords = []
        self.saved_outbox = []

        async def _by_email(email):
            return self._by_email(email) if callable(self._by_email) else self._by_email

        async def _by_id(user_id):
            return self._by_id(user_id) if callable(self._by_id) else self._by_id

        async def _next_id():
            return self._next_id

        async def _save_user(user):
            self.saved_users.append(user)

        async def _save_version(user, event, editor_id):
            self.version_saved.append((user, event, editor_id))

        async def _save_password(user, hashed):
            self.saved_passwords.append((user, hashed))

        async def _not_published_versions():
            return []

        async def _batch_save(users):
            self.saved_outbox = users

        self.user_repositories = SimpleNamespace(
            read=SimpleNamespace(by_email=_by_email, by_id=_by_id, next_id=_next_id, save=_save_user),
            version=SimpleNamespace(save=_save_version),
            outbox=SimpleNamespace(not_published_versions=_not_published_versions, batch_save=_batch_save),
        )
        self.user_password_repositories = SimpleNamespace(read=SimpleNamespace(save=_save_password))

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None


@pytest.mark.asyncio
async def test_create_user_success(user_factory):
    next_id = user_factory().user_id
    uow = _FakeUow(by_email=None, next_id=next_id)
    kv = SimpleNamespace(get_int=lambda key: 123456)

    async def get_int(_: str):
        return 123456

    async def validate(_: str):
        return None

    async def hash_pwd(_: str):
        return "hashed"

    pwd = SimpleNamespace(validate=validate, hash=hash_pwd)
    kv.get_int = get_int

    dto = await UserCreatingUseCase(uow, kv, pwd).execute(
        UserCreatingCommand(email="a@a.a", code=123456, password="password")
    )

    assert dto.email == "a@a.a"
    assert len(uow.saved_users) == 1
    assert uow.version_saved[0][1] == UserEvent.CREATED
    assert uow.saved_passwords[0][1] == "hashed"


@pytest.mark.asyncio
async def test_create_user_invalid_code(user_factory):
    uow = _FakeUow(by_email=None, next_id=user_factory().user_id)

    async def get_int(_: str):
        return 111111

    kv = SimpleNamespace(get_int=get_int)

    async def validate(_: str):
        return None

    async def hash_pwd(_: str):
        return "hashed"

    pwd = SimpleNamespace(validate=validate, hash=hash_pwd)

    with pytest.raises(AppInvalidDataError):
        await UserCreatingUseCase(uow, kv, pwd).execute(
            UserCreatingCommand(email="a@a.a", code=123456, password="password")
        )


@pytest.mark.asyncio
async def test_auth_code_send_and_auth(user_factory):
    user = user_factory()
    uow = _FakeUow(by_email=user)
    storage = {}

    async def set_value(key: str, value: int, ttl: timedelta):
        storage[key] = value

    async def get_int(key: str):
        return storage.get(key)

    kv = SimpleNamespace(set=set_value, get_int=get_int)
    rng = SimpleNamespace(number=lambda n: None)

    async def number(_: int):
        return 87654321

    async def auth_code(code: int):
        return f"code:{code}"

    async def send(emails, body):
        return None

    rng.number = number
    builder = SimpleNamespace(auth_code=auth_code)
    sender = SimpleNamespace(send=send)

    await AuthCodeSendingUseCase(uow, kv, rng, sender, builder).execute(
        AuthCodeSendingCommand(email=user.email.email)
    )
    dto = await CodeAuthUseCase(uow, kv).execute(
        CodeAuthCommand(email=user.email.email, code=87654321)
    )

    assert dto.user_id == user.user_id.user_id


@pytest.mark.asyncio
async def test_confirm_email_fails_if_exists(user_factory):
    uow = _FakeUow(by_email=user_factory())

    async def number(_: int):
        return 12345678

    async def set_value(*args):
        return None

    async def send(*args):
        return None

    async def confirm_email(code: int):
        return f"{code}"

    uc = UserConfirmingEmailUseCase(
        uow,
        SimpleNamespace(set=set_value),
        SimpleNamespace(send=send),
        SimpleNamespace(confirm_email=confirm_email),
        SimpleNamespace(number=number),
    )

    with pytest.raises(AppInvalidDataError):
        await uc.execute(UserConfirmingEmailCommand(email="e@e.e"))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("uc_class", "command_factory"),
    [
        (
            UserFreezingUseCase,
            lambda initiator_id, user_id: UserFreezingCommand(
                initiator_id=initiator_id, user_id=user_id
            ),
        ),
        (
            UserAppointingAdminUseCase,
            lambda initiator_id, user_id: UserAppointingAdminCommand(
                initiator_id=initiator_id, user_id=user_id
            ),
        ),
        (
            UserAppointingUserUseCase,
            lambda initiator_id, user_id: UserAppointingUserCommand(
                initiator_id=initiator_id, user_id=user_id
            ),
        ),
    ],
    ids=["freeze", "appoint_admin", "appoint_user"],
)
async def test_staff_commands_success(user_factory, uc_class, command_factory):
    initiator = user_factory(status=UserStatus.ADMIN)
    target_status = UserStatus.ADMIN if uc_class is UserAppointingUserUseCase else UserStatus.USER
    target = user_factory(status=target_status)
    uow = _FakeUow(by_id=lambda user_id: initiator if user_id == initiator.user_id else target)

    dto = await uc_class(uow).execute(
        command_factory(initiator.user_id.user_id, target.user_id.user_id)
    )

    assert dto.user_id == target.user_id.user_id
    assert uow.version_saved[0][1] == UserEvent.UPDATED


@pytest.mark.asyncio
async def test_staff_command_not_found(user_factory):
    initiator = user_factory(status=UserStatus.ADMIN)
    uow = _FakeUow(by_id=lambda user_id: initiator if user_id == initiator.user_id else None)

    with pytest.raises(AppNotFoundError):
        await UserFreezingUseCase(uow).execute(
            UserFreezingCommand(initiator_id=initiator.user_id.user_id, user_id=uuid4())
        )


@pytest.mark.asyncio
async def test_confirm_new_email_and_change_email(user_factory):
    initiator = user_factory(status=UserStatus.ADMIN)
    uow = _FakeUow(by_id=initiator, by_email=None)
    storage = {}

    async def set_value(key: str, value: int, ttl: timedelta):
        storage[key] = value

    async def get_int(key: str):
        return storage.get(key)

    async def number(_: int):
        return 22222222

    async def send(emails, body):
        return None

    async def confirm_new_email(code: int):
        return f"code:{code}"

    kv = SimpleNamespace(set=set_value, get_int=get_int)
    rng = SimpleNamespace(number=number)
    sender = SimpleNamespace(send=send)
    builder = SimpleNamespace(confirm_new_email=confirm_new_email)

    await NewEmailConfirmingUseCase(uow, kv, rng, sender, builder).execute(
        NewEmailConfirmingCommand(
            initiator_id=initiator.user_id.user_id,
            new_email="new@example.com",
        )
    )

    assert storage["users:confirm_new_email:user@example.com"] == 22222222
    assert storage["users:confirm_new_email:new@example.com"] == 22222222

    initiator_for_change = user_factory(status=UserStatus.ADMIN, email="old@example.com")
    uow_for_change = _FakeUow(by_id=initiator_for_change, by_email=None)
    storage_for_change = {
        "users:confirm_new_email:new2@example.com": 33333333,
        "users:confirm_new_email:old@example.com": 44444444,
    }

    async def get_int_change(key: str):
        return storage_for_change.get(key)

    dto = await UserEmailChangingUseCase(
        uow_for_change, SimpleNamespace(get_int=get_int_change)
    ).execute(
        UserEmailChangingCommand(
            initiator_id=initiator_for_change.user_id.user_id,
            new_email="new2@example.com",
            new_email_code=33333333,
            old_email_code=44444444,
        )
    )

    assert dto.email == "new2@example.com"


@pytest.mark.asyncio
async def test_private_publication_use_case_batches(user_factory):
    users = [user_factory(), user_factory()]
    dtos = [SimpleNamespace(user=user) for user in users]
    uow = _FakeUow()

    async def not_published_versions():
        return dtos

    uow.user_repositories.outbox.not_published_versions = not_published_versions
    published = {"items": None}

    async def batch_publish(items):
        published["items"] = items

    publisher = SimpleNamespace(batch_publish=batch_publish)

    await UserPublicationUseCase(uow, publisher).execute()

    assert published["items"] == dtos
    assert uow.saved_outbox == users
