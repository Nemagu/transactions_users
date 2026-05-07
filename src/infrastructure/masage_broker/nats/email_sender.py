from nats.aio.client import Client

from application.errors import AppInternalError
from application.ports.email import EmailMessage, EmailSender
from infrastructure.config.nats import NatsEmailSettings
from infrastructure.masage_broker.nats.payload import EmailSendPayload


class NatsEmailSender(EmailSender):
    def __init__(self, nats_client: Client, settings: NatsEmailSettings) -> None:
        self._nc = nats_client
        self._settings = settings

    async def send(self, message: EmailMessage) -> None:
        """Сериализует письмо в payload и публикует в NATS."""
        payload = EmailSendPayload(
            recipient=message.recipient.email,
            subject=message.subject,
            html_body=message.html_body,
            text_body=message.text_body,
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
