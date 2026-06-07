"""In-memory message queue with fallback (no RabbitMQ dependency)."""

import asyncio
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, List


@dataclass
class Message:
    """Message wrapper."""

    exchange: str
    routing_key: str
    body: dict
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class InMemoryMessageQueue:
    """
    In-memory message queue with fallback support.
    No external dependencies - uses asyncio and in-memory storage.
    """

    def __init__(self):
        self.messages: List[Message] = []
        self.subscribers: defaultdict[str, List[Callable]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def publish(self, exchange: str, routing_key: str, body: dict) -> bool:
        """Publish a message."""
        try:
            message = Message(
                exchange=exchange,
                routing_key=routing_key,
                body=body,
            )

            async with self._lock:
                self.messages.append(message)

            # Trigger subscribers
            subscription_key = f"{exchange}.{routing_key}"
            if subscription_key in self.subscribers:
                for callback in self.subscribers[subscription_key]:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(message)
                        else:
                            callback(message)
                    except Exception as e:
                        print(f"Error in message callback: {e}")

            return True
        except Exception as e:
            print(f"Error publishing message: {e}")
            return False

    async def subscribe(self, exchange: str, routing_key: str, callback: Callable) -> str:
        """Subscribe to messages."""
        subscription_key = f"{exchange}.{routing_key}"
        self.subscribers[subscription_key].append(callback)
        return subscription_key

    def get_messages(self, exchange: str = None, routing_key: str = None) -> List[Message]:
        """Retrieve stored messages (for logging/debugging)."""
        if not exchange:
            return self.messages

        filtered = [
            m
            for m in self.messages
            if m.exchange == exchange and (routing_key is None or m.routing_key == routing_key)
        ]
        return filtered

    async def clear(self):
        """Clear all messages."""
        async with self._lock:
            self.messages.clear()


# Global message queue instance
message_queue = InMemoryMessageQueue()
