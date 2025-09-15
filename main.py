from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas import AddItemRequest, SuccessResponse, ErrorResponse
from app.services.order_service import OrderService
from contextlib import asynccontextmanager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("Starting Order Service")
    yield
    # Shutdown logic
    logger.info("Shutting down Order Service")


app = FastAPI(
    title="Order Service API",
    description="Сервис для управления заказами и товарами",
    version="1.0.0",
    lifespan=lifespan
)


@app.post(
    "/orders/{order_id}/items",
    response_model=SuccessResponse,
    responses={
        200: {"description": "Товар успешно добавлен в заказ"},
        400: {"model": ErrorResponse, "description": "Недостаточно товара на складе"},
        404: {"model": ErrorResponse, "description": "Заказ или товар не найден"},
        500: {"model": ErrorResponse, "description": "Внутренняя ошибка сервера"}
    }
)
async def add_item_to_order(
        request: AddItemRequest,
        db: AsyncSession = Depends(get_db)
):
    """
    Добавить товар в заказ.

    - Если товар уже есть в заказе, увеличивает его количество
    - Если товара нет в наличии, возвращает ошибку
    - Автоматически обновляет цену товара в заказе
    """
    try:
        order_service = OrderService(db)
        result, error = await order_service.add_item_to_order(request)

        if error:
            error_messages = {
                "ORDER_NOT_FOUND": "Заказ не найден",
                "PRODUCT_NOT_FOUND": "Товар не найден",
                "INSUFFICIENT_STOCK": "Недостаточно товара на складе"
            }
            error_code = error.upper()
            detail = error_messages.get(error_code, "Неизвестная ошибка")

            if error_code == "INSUFFICIENT_STOCK":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=detail
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=detail
                )

        # Обновляем количество товара на складе
        success = await order_service.update_product_stock(request.product_id, request.quantity)
        if not success:
            logger.error(f"Failed to update stock for product {request.product_id}")

        return SuccessResponse(
            message="Товар успешно добавлен в заказ",
            order_item=result
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера"
        )


@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {"status": "healthy", "service": "order-service"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)