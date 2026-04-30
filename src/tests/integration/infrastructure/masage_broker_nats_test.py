from datetime import datetime, timezone
from uuid import uuid7

import pytest

from application.ports.repositories import UserEvent, UserVersionDTO
from domain.user import Email, UserFactory, UserID
from infrastructure.config.nats import NatsEmailSettings, NatsPublisherStreamSettings
from infrastructure.masage_broker.nats.email_sender import NatsEmailSender
from infrastructure.masage_broker.nats.publisher import EventNatsPublisher


@pytest.mark.asyncio
async def test_nats_email_sender_publishes_payload(nats_client) -> None:
    sender = NatsEmailSender(nats_client=nats_client, settings=NatsEmailSettings())
    sub = await nats_client.subscribe("email.send")

    await sender.send([Email("a@b.c")], "hello")
    msg = await sub.next_msg(timeout=2)

    assert b'"recipients":["a@b.c"]' in msg.data
    assert b'"body":"hello"' in msg.data


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("event", "subject"),
    [
        (UserEvent.CREATED, "users.user.created"),
        (UserEvent.UPDATED, "users.user.updated"),
        (UserEvent.FROZEN, "users.user.frozen"),
        (UserEvent.DELETED, "users.user.deleted"),
        (UserEvent.RESTORED, "users.user.restored"),
    ],
    ids=["created", "updated", "frozen", "deleted", "restored"],
)
async def test_event_nats_publisher_subjects(
    nats_jetstream, event: UserEvent, subject: str
) -> None:
    await nats_jetstream.add_stream(name="users", subjects=["users.user.*"])
    sub = await nats_jetstream.subscribe(subject)

    user = UserFactory.new(
        user_id=UserID(uuid7()),
        email=Email("pub@example.com"),
    )
    dto = UserVersionDTO(
        user=user,
        event=event,
        editor_id=None,
        created_at=datetime.now(tz=timezone.utc),
    )
    publisher = EventNatsPublisher(
        stream_settings=NatsPublisherStreamSettings(),
        nc=None,
        js=nats_jetstream,
    )

    await publisher.publish(dto)
    msg = await sub.next_msg(timeout=2)

    assert msg.subject == subject
    assert b'"email":"pub@example.com"' in msg.data
