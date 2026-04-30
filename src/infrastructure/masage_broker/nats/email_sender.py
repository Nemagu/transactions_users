from nats.aio.client import Client

from application.errors import AppInternalError
from application.ports.email import EmailSender
from domain.user import Email
from infrastructure.config.nats import NatsEmailSettings
from infrastructure.masage_broker.nats.payload import EmailSendPayload


class NatsEmailSender(EmailSender):
    def __init__(self, nats_client: Client, settings: NatsEmailSettings) -> None:
        self._nc = nats_client
        self._settings = settings

    async def send(self, recipients: list[Email], body: str) -> None:
        """Отправляет тело письма во внешний email-сервис через NATS."""
        payload = EmailSendPayload(
            recipients=[email.email for email in recipients],
            body=body,
        )
        data = payload.model_dump_json().encode("utf-8")
        try:
            await self._nc.publish(subject=self._settings.send_subject, payload=data)
        except Exception as err:
            raise AppInternalError(
                msg="ошибка отправки сообщения в email сервис через nats",
                action="отправка email через nats",
                wrap_error=err,
            ) from err
