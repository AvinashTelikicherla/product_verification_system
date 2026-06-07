"""Product mapper for entity conversions."""

from datetime import datetime
from uuid import uuid4

from src.models.db_entities.product_entity import ProductEntity
from src.models.db_models import ProductModel
from src.models.response_schemas import ProductResponse


class ProductMapper:
    """Map Product entities to models and responses."""

    @staticmethod
    def entity_to_model(entity: ProductEntity) -> ProductModel:
        return ProductModel(
            id=entity.id,
            wid=entity.wid,
            ean=entity.ean,
            manufacturing_date=entity.manufacturing_date,
            expiry_date=entity.expiry_date,
            batch_id=entity.batch_id,
            quantity=entity.quantity,
            location=entity.location,
            upload_job_id=entity.upload_job_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    @staticmethod
    def entity_to_response(entity: ProductEntity) -> ProductResponse:
        is_expired = entity.expiry_date < datetime.utcnow()

        return ProductResponse(
            id=entity.id,
            wid=entity.wid,
            ean=entity.ean,
            manufacturing_date=entity.manufacturing_date,
            expiry_date=entity.expiry_date,
            batch_id=entity.batch_id,
            quantity=entity.quantity,
            location=entity.location,
            is_expired=is_expired,
            created_at=entity.created_at,
        )

    @staticmethod
    def create_entity_from_data(
        wid: str,
        ean: str,
        manufacturing_date: datetime,
        expiry_date: datetime,
        batch_id: str = None,
        quantity: int = 1,
        location: str = None,
        upload_job_id: str = None,
    ) -> ProductEntity:
        return ProductEntity(
            id=str(uuid4()),
            wid=wid,
            ean=ean,
            manufacturing_date=manufacturing_date,
            expiry_date=expiry_date,
            batch_id=batch_id,
            quantity=quantity,
            location=location,
            upload_job_id=upload_job_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
