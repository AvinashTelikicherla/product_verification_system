"""Product service for business logic."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.mappers.product_mapper import ProductMapper
from src.models.response_schemas import ProductResponse
from src.repositories.product_repository import ProductRepository


class ProductService:
    """Service for product management."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = ProductRepository(session)
        self.mapper = ProductMapper()

    async def create_product(
        self,
        wid: str,
        ean: str,
        manufacturing_date: datetime,
        expiry_date: datetime,
        batch_id: str = None,
        quantity: int = 1,
        location: str = None,
        upload_job_id: str = None,
    ) -> ProductResponse:
        """Create a new product."""
        # Check if product with same WID exists
        existing = await self.repository.get_by_wid(wid)
        if existing:
            raise ValueError(f"Product with WID '{wid}' already exists")

        # Create product
        product_entity = self.mapper.create_entity_from_data(
            wid, ean, manufacturing_date, expiry_date, batch_id, quantity, location, upload_job_id
        )
        created = await self.repository.create(product_entity)

        return self.mapper.entity_to_response(created)

    async def get_product(self, product_id: str) -> Optional[ProductResponse]:
        """Get product by ID."""
        product = await self.repository.get_by_id(product_id)
        if not product:
            return None
        return self.mapper.entity_to_response(product)

    async def get_product_by_wid(self, wid: str) -> Optional[ProductResponse]:
        """Get product by warehouse ID."""
        product = await self.repository.get_by_wid(wid)
        if not product:
            return None
        return self.mapper.entity_to_response(product)

    async def get_all_products(self, skip: int = 0, limit: int = 100) -> List[ProductResponse]:
        """Get all products."""
        products = await self.repository.get_all(skip, limit)
        return [self.mapper.entity_to_response(p) for p in products]

    async def bulk_create_products(
        self, products_data: List[dict], upload_job_id: str = None
    ) -> tuple[int, int]:
        """
        Bulk create products from data.

        Returns:
            Tuple of (created_count, error_count)
        """
        created_count = 0
        error_count = 0

        for product_data in products_data:
            try:
                await self.create_product(
                    wid=product_data["wid"],
                    ean=product_data["ean"],
                    manufacturing_date=product_data["manufacturing_date"],
                    expiry_date=product_data["expiry_date"],
                    batch_id=product_data.get("batch_id"),
                    quantity=product_data.get("quantity", 1),
                    location=product_data.get("location"),
                    upload_job_id=upload_job_id,
                )
                created_count += 1
            except Exception as e:
                print(f"Error creating product: {e}")
                error_count += 1

        return created_count, error_count

    async def get_products_by_upload_job(self, job_id: str) -> List[ProductResponse]:
        """Get all products from an upload job."""
        products = await self.repository.get_by_upload_job(job_id)
        return [self.mapper.entity_to_response(p) for p in products]
