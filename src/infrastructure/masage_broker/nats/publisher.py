from collections.abc import Sequence

from nats.aio.client import Client
from nats.js import JetStreamContext
from pydantic import ValidationError

from application.errors import AppInternalError
from application.ports.event_publisher import EventPublisher, PublishEventDTO
from infrastructure.config import NatsPublisherStreamSettings
from infrastructure.config.nats import BaseNatsPublisherStreamSettings
from infrastructure.masage_broker.nats.payload import UserPayload


class EventNatsPublisher(EventPublisher):
    def __init__(
        self,
        stream_settings: NatsPublisherStreamSettings,
        nc: Client,
        js: JetStreamContext,
    ) -> None:
        self._stream = stream_settings
        self._nc = nc
        self._js = js

    async def publish(self, event: PublishEventDTO) -> None:
        """Публикует одно событие в NATS."""
        subject, payload = self._subject_payload(event)
        await self._js.publish(subject=subject, payload=payload)

    async def batch_publish(self, events: Sequence[PublishEventDTO]) -> None:
        """Публикует пачку событий в NATS."""
        for event in events:
            await self.publish(event)

    def _subject_payload(self, event: PublishEventDTO) -> tuple[str, bytes]:
        try:
            payload_model = UserPayload.from_dto(event)
            payload = payload_model.model_dump_json().encode()
        except ValidationError as err:
            raise AppInternalError(
                msg="ошибка валидации pydantic при формировании payload",
                action="формирование payload для публикации события пользователя",
                data={"event": event.event.value},
                wrap_error=err,
            ) from err
        return self._subject(event=event, stream=self._stream.user), payload

    def _subject(
        self, event: PublishEventDTO, stream: BaseNatsPublisherStreamSettings
    ) -> str:
        match event.event.value:
            case "created":
                return stream.creation_subject
            case "updated":
                return stream.update_subject
            case "frozen":
                return stream.frozen_subject
            case "deleted":
                return stream.deletion_subject
            case "restored":
                return stream.restoration_subject
            case _:
                raise AppInternalError(
                    msg="получено неподдерживаемое событие для публикации",
                    action="определение subject для публикации",
                    data={"event": event.event.value},
                )
