"""Background workers слоя представления."""

from presentation.background.nats import NatsPublisherWorker

__all__ = ["NatsPublisherWorker"]
