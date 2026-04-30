from uuid import UUID

from fastapi import APIRouter, Depends

from application.command.public.user import (
    AuthCodeSendingUseCase,
    CodeAuthUseCase,
    NewEmailConfirmingUseCase,
    PasswordAuthUseCase,
    UserAppointingAdminCommand,
    UserAppointingAdminUseCase,
    UserAppointingUserCommand,
    UserAppointingUserUseCase,
    UserConfirmingEmailUseCase,
    UserCreatingUseCase,
    UserEmailChangingUseCase,
    UserFreezingCommand,
    UserFreezingUseCase,
)
from infrastructure.db.postgres import PostgresUnitOfWork
from infrastructure.email import SimpleEmailBodyBuilder
from infrastructure.key_value.redis import RedisKeyValueStore
from infrastructure.masage_broker.nats import NatsEmailSender
from infrastructure.password_manager import Argon2PasswordManager
from infrastructure.randomizer import SecureRandomizer
from presentation.api.dependencies import (
    db_unit_of_work,
    email_builder,
    email_sender,
    password_manager,
    randomizer,
    redis_store,
    user_id_extractor,
)
from presentation.api.models.user import (
    AuthCodeRequest,
    AuthCodeSendRequest,
    AuthPasswordRequest,
    ChangeEmailRequest,
    ConfirmNewEmailRequest,
    UserConfirmEmailRequest,
    UserCreateRequest,
    UserSimpleResponse,
)

user_router = APIRouter(prefix="/users", tags=["User"])


@user_router.post("/confirm-email")
async def confirm_email(
    request: UserConfirmEmailRequest,
    uow: PostgresUnitOfWork = Depends(db_unit_of_work),
    key_value_store: RedisKeyValueStore = Depends(redis_store),
    sender: NatsEmailSender = Depends(email_sender),
    builder: SimpleEmailBodyBuilder = Depends(email_builder),
    rng: SecureRandomizer = Depends(randomizer),
) -> None:
    uc = UserConfirmingEmailUseCase(uow, key_value_store, sender, builder, rng)
    await uc.execute(request.to_command())


@user_router.post("")
async def create_user(
    request: UserCreateRequest,
    uow: PostgresUnitOfWork = Depends(db_unit_of_work),
    key_value_store: RedisKeyValueStore = Depends(redis_store),
    pwd_manager: Argon2PasswordManager = Depends(password_manager),
) -> UserSimpleResponse:
    uc = UserCreatingUseCase(uow, key_value_store, pwd_manager)
    dto = await uc.execute(request.to_command())
    return UserSimpleResponse.from_dto(dto)


@user_router.post("/auth/send-code")
async def send_auth_code(
    request: AuthCodeSendRequest,
    uow: PostgresUnitOfWork = Depends(db_unit_of_work),
    key_value_store: RedisKeyValueStore = Depends(redis_store),
    rng: SecureRandomizer = Depends(randomizer),
    sender: NatsEmailSender = Depends(email_sender),
    builder: SimpleEmailBodyBuilder = Depends(email_builder),
) -> None:
    uc = AuthCodeSendingUseCase(uow, key_value_store, rng, sender, builder)
    await uc.execute(request.to_command())


@user_router.post("/auth/code")
async def code_auth(
    request: AuthCodeRequest,
    uow: PostgresUnitOfWork = Depends(db_unit_of_work),
    key_value_store: RedisKeyValueStore = Depends(redis_store),
) -> UserSimpleResponse:
    uc = CodeAuthUseCase(uow, key_value_store)
    dto = await uc.execute(request.to_command())
    return UserSimpleResponse.from_dto(dto)


@user_router.post("/auth/password")
async def password_auth(
    request: AuthPasswordRequest,
    uow: PostgresUnitOfWork = Depends(db_unit_of_work),
    pwd_manager: Argon2PasswordManager = Depends(password_manager),
) -> UserSimpleResponse:
    uc = PasswordAuthUseCase(uow, pwd_manager)
    dto = await uc.execute(request.to_command())
    return UserSimpleResponse.from_dto(dto)


@user_router.post("/email/confirm-new")
async def confirm_new_email(
    request: ConfirmNewEmailRequest,
    initiator_id: UUID = Depends(user_id_extractor),
    uow: PostgresUnitOfWork = Depends(db_unit_of_work),
    key_value_store: RedisKeyValueStore = Depends(redis_store),
    rng: SecureRandomizer = Depends(randomizer),
    sender: NatsEmailSender = Depends(email_sender),
    builder: SimpleEmailBodyBuilder = Depends(email_builder),
) -> None:
    uc = NewEmailConfirmingUseCase(uow, key_value_store, rng, sender, builder)
    await uc.execute(request.to_command(initiator_id))


@user_router.put("/email")
async def change_email(
    request: ChangeEmailRequest,
    initiator_id: UUID = Depends(user_id_extractor),
    uow: PostgresUnitOfWork = Depends(db_unit_of_work),
    key_value_store: RedisKeyValueStore = Depends(redis_store),
) -> UserSimpleResponse:
    uc = UserEmailChangingUseCase(uow, key_value_store)
    dto = await uc.execute(request.to_command(initiator_id))
    return UserSimpleResponse.from_dto(dto)


@user_router.put("/{user_id}/freeze")
async def freeze_user(
    user_id: UUID,
    initiator_id: UUID = Depends(user_id_extractor),
    uow: PostgresUnitOfWork = Depends(db_unit_of_work),
) -> UserSimpleResponse:
    uc = UserFreezingUseCase(uow)
    dto = await uc.execute(UserFreezingCommand(initiator_id=initiator_id, user_id=user_id))
    return UserSimpleResponse.from_dto(dto)


@user_router.put("/{user_id}/appoint-admin")
async def appoint_admin(
    user_id: UUID,
    initiator_id: UUID = Depends(user_id_extractor),
    uow: PostgresUnitOfWork = Depends(db_unit_of_work),
) -> UserSimpleResponse:
    uc = UserAppointingAdminUseCase(uow)
    dto = await uc.execute(
        UserAppointingAdminCommand(initiator_id=initiator_id, user_id=user_id)
    )
    return UserSimpleResponse.from_dto(dto)


@user_router.put("/{user_id}/appoint-user")
async def appoint_user(
    user_id: UUID,
    initiator_id: UUID = Depends(user_id_extractor),
    uow: PostgresUnitOfWork = Depends(db_unit_of_work),
) -> UserSimpleResponse:
    uc = UserAppointingUserUseCase(uow)
    dto = await uc.execute(
        UserAppointingUserCommand(initiator_id=initiator_id, user_id=user_id)
    )
    return UserSimpleResponse.from_dto(dto)
