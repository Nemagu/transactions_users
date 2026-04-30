from infrastructure.config.nats import (
    NatsEmailSettings,
    NatsPublisherStreamSettings,
    NatsSettings,
)


def test_nats_email_subjects() -> None:
    settings = NatsEmailSettings(stream_name="email", send_subject_name="send")

    assert settings.send_subject == "email.send"
    assert settings.subjects == ["email.send"]


def test_nats_publisher_user_subjects() -> None:
    stream = NatsPublisherStreamSettings().user

    assert stream.creation_subject == "users.user.created"
    assert stream.update_subject == "users.user.updated"
    assert stream.frozen_subject == "users.user.frozen"
    assert stream.deletion_subject == "users.user.deleted"
    assert stream.restoration_subject == "users.user.restored"


def test_nats_settings_url() -> None:
    settings = NatsSettings(host="nats.local", port=4223)

    assert settings.url == "nats://nats.local:4223"
