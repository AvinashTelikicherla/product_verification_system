"""Message publisher base class."""

from src.mq_messaging.connection import message_queue


class Publisher:
    """Base publisher for message queue events."""

    def __init__(self):
        self.message_queue = message_queue

    async def publish(self, exchange: str, routing_key: str, body: dict) -> bool:
        """Publish a message to the queue."""
        return await self.message_queue.publish(exchange, routing_key, body)
