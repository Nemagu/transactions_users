from application.command.base import PublicationUseCase


class UserPublicationUseCase(PublicationUseCase):
    async def execute(self) -> None:
        async with self._uow as uow:
            user_dtos = await uow.user_repositories.outbox.not_published_versions()
            await self._event_publisher.batch_publish(user_dtos)
            await uow.user_repositories.outbox.batch_save([d.user for d in user_dtos])
