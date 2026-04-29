from domain.errors import EntityAlreadyExistsError
from domain.user.repositories import UserReadRepository
from domain.user.value_objects import Email


class UserUniquenessService:
    def __init__(self, read_repository: UserReadRepository) -> None:
        self._read_repo = read_repository

    async def validate_email(self, email: Email) -> None:
        existing_user = await self._read_repo.by_email(email)
        if existing_user:
            raise EntityAlreadyExistsError(
                msg="такой email уже существует",
                struct_name=existing_user.aggregate_name.name,
                data={
                    "user": {
                        "user_id": existing_user.user_id.user_id,
                        "email": existing_user.email.email,
                    }
                },
            )
