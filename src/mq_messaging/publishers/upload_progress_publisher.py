"""Upload progress publisher."""

from datetime import datetime

from src.mq_messaging.publisher import Publisher


class UploadProgressPublisher(Publisher):
    """Publisher for CSV upload progress events."""

    async def publish_progress(
        self, job_id: str, status: str, processed_rows: int, total_rows: int
    ) -> bool:
        """Publish upload progress event."""
        progress_percentage = int((processed_rows / total_rows * 100)) if total_rows > 0 else 0

        body = {
            "job_id": job_id,
            "status": status,
            "processed_rows": processed_rows,
            "total_rows": total_rows,
            "progress_percentage": progress_percentage,
            "timestamp": datetime.utcnow().isoformat(),
        }

        return await self.publish(exchange="uploads", routing_key="progress", body=body)
