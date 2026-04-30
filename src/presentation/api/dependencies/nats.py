from fastapi import Request

from infrastructure.masage_broker.nats import NatsEmailSender


async def email_sender(request: Request) -> NatsEmailSender:
    return NatsEmailSender(
        request.app.state.nats_connection_manager.client(),
        request.app.state.worker_settings.email,
    )
