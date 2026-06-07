"""Product repository — data access for the products table."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.db_entities.product_entity import ProductEntity


class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, product: ProductEntity) -> ProductEntity:
        self.session.add(product)
        await self.session.commit()
        await self.session.refresh(product)
        return product

    async def create_many(self, products: List[ProductEntity]) -> List[ProductEntity]:
        self.session.add_all(products)
        await self.session.commit()
        return products

    async def get_by_id(self, product_id: str) -> Optional[ProductEntity]:
        result = await self.session.execute(
            select(ProductEntity).where(ProductEntity.id == product_id)
        )
        return result.scalar_one_or_none()

    async def get_by_wid(self, wid: str) -> Optional[ProductEntity]:
        result = await self.session.execute(select(ProductEntity).where(ProductEntity.wid == wid))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ProductEntity]:
        result = await self.session.execute(select(ProductEntity).offset(skip).limit(limit))
        return result.scalars().all()

    async def get_by_upload_job(self, job_id: str) -> List[ProductEntity]:
        result = await self.session.execute(
            select(ProductEntity).where(ProductEntity.upload_job_id == job_id)
        )
        return result.scalars().all()

    async def update(self, product: ProductEntity) -> ProductEntity:
        await self.session.merge(product)
        await self.session.commit()
        return product

    async def delete(self, product_id: str) -> bool:
        product = await self.get_by_id(product_id)
        if product:
            await self.session.delete(product)
            await self.session.commit()
            return True
        return False
