"""Dependency-injection container.

Wires together shared resources and services using the ``dependency-injector``
library:

* **Singleton** providers hold application-lifetime resources that must be
  shared across every request — the database manager, the in-memory message
  queue, and the upload-progress publisher.
* **Factory** providers build a fresh service instance per request, bound to
  the request-scoped database session passed in at call time, e.g.
  ``container.user_service(session)``.

Centralising construction here means a route never news-up a service directly,
and a test can swap any provider via ``container.<provider>.override(...)``.
"""

from dependency_injector import containers, providers

from src.database import db_manager
from src.mq_messaging.connection import message_queue
from src.mq_messaging.publishers.upload_progress_publisher import UploadProgressPublisher
from src.services.product_service import ProductService
from src.services.upload_service import UploadService
from src.services.user_service import UserService
from src.services.verification_service import VerificationService


class Container(containers.DeclarativeContainer):
    """Application container."""

    # --- Singletons: shared, application-lifetime resources ---
    database = providers.Object(db_manager)
    message_queue = providers.Object(message_queue)
    upload_publisher = providers.Singleton(UploadProgressPublisher)

    # --- Factories: per-request services bound to a session at call time ---
    user_service = providers.Factory(UserService)
    product_service = providers.Factory(ProductService)
    verification_service = providers.Factory(VerificationService)
    upload_service = providers.Factory(UploadService, publisher=upload_publisher)


# Application-wide singleton container instance.
container = Container()
