from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert
from sqlalchemy.exc import SQLAlchemyError
from app.models import Order, Product, OrderItem
from app.schemas import AddItemRequest, OrderItemResponse
from typing import Tuple, Optional


class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_item_to_order(self, request: AddItemRequest) -> Tuple[Optional[OrderItemResponse], Optional[str]]:
        try:
            # Проверяем существование заказа
            order = await self.db.get(Order, request.order_id)
            if not order:
                return None, "ORDER_NOT_FOUND"

            # Проверяем существование товара и доступное количество
            product = await self.db.get(Product, request.product_id)
            if not product:
                return None, "PRODUCT_NOT_FOUND"

            if product.quantity < request.quantity:
                return None, "INSUFFICIENT_STOCK"

            # Проверяем, есть ли уже этот товар в заказе
            existing_item_query = select(OrderItem).where(
                OrderItem.order_id == request.order_id,
                OrderItem.product_id == request.product_id
            )
            existing_item = (await self.db.execute(existing_item_query)).scalar_one_or_none()

            if existing_item:
                # Обновляем существующую позицию
                new_quantity = existing_item.quantity + request.quantity
                stmt = update(OrderItem).where(
                    OrderItem.id == existing_item.id
                ).values(
                    quantity=new_quantity,
                    price=product.price
                )
                await self.db.execute(stmt)
                await self.db.commit()

                # Обновляем объект для возврата
                await self.db.refresh(existing_item)
                return OrderItemResponse.model_validate(existing_item), None
            else:
                # Создаем новую позицию
                new_item = OrderItem(
                    order_id=request.order_id,
                    product_id=request.product_id,
                    quantity=request.quantity,
                    price=product.price
                )
                self.db.add(new_item)
                await self.db.commit()
                await self.db.refresh(new_item)

                return OrderItemResponse.model_validate(new_item), None

        except SQLAlchemyError as e:
            await self.db.rollback()
            raise e

    async def update_product_stock(self, product_id: int, quantity: int) -> bool:
        try:
            # Уменьшаем количество товара на складе
            stmt = update(Product).where(
                Product.id == product_id
            ).values(
                quantity=Product.quantity - quantity
            )
            await self.db.execute(stmt)
            await self.db.commit()
            return True
        except SQLAlchemyError:
            await self.db.rollback()
            return False