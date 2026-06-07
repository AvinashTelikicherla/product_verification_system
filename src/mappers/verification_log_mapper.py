"""Verification log mapper — entity <-> model <-> response conversions."""

from datetime import datetime
from uuid import uuid4

from src.models.db_entities.verification_log_entity import VerificationLogEntity
from src.models.db_models import VerificationLogModel
from src.models.response_schemas import VerificationLogResponse


class VerificationLogMapper:
    @staticmethod
    def entity_to_model(entity: VerificationLogEntity) -> VerificationLogModel:
        return VerificationLogModel(
            id=entity.id,
            product_id=entity.product_id,
            operator_id=entity.operator_id,
            image_path=entity.image_path,
            expiry_extracted=entity.expiry_extracted,
            expiry_is_valid=(
                entity.expiry_is_valid.lower() == "true" if entity.expiry_is_valid else None
            ),
            notes=entity.notes,
            verification_status=entity.verification_status,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    @staticmethod
    def entity_to_response(entity: VerificationLogEntity) -> VerificationLogResponse:
        return VerificationLogResponse(
            id=entity.id,
            product_id=entity.product_id,
            operator_id=entity.operator_id,
            image_path=entity.image_path,
            expiry_extracted=entity.expiry_extracted,
            expiry_is_valid=(
                entity.expiry_is_valid.lower() == "true" if entity.expiry_is_valid else None
            ),
            notes=entity.notes,
            verification_status=entity.verification_status,
            created_at=entity.created_at,
        )

    @staticmethod
    def create_entity(
        product_id: str,
        operator_id: str,
        image_path: str = None,
        expiry_extracted: str = None,
        notes: str = None,
    ) -> VerificationLogEntity:
        return VerificationLogEntity(
            id=str(uuid4()),
            product_id=product_id,
            operator_id=operator_id,
            image_path=image_path,
            expiry_extracted=expiry_extracted,
            notes=notes,
            verification_status="pending",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
