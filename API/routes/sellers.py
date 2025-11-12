"""
Маршруты для работы с продавцами с кэшированием
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Dict, Any
from sqlalchemy.orm import Session
import logging
from pydantic import BaseModel, EmailStr

from database.connection import DatabaseConnection
from database.models import Supplier
from database.odt import SupplierODT, ODTConverter
from cache import cached, invalidate_cache, cache
from background_tasks import send_statistics_email

logger = logging.getLogger(__name__)

# Создаем роутер
router = APIRouter(prefix="/sallers", tags=["sallers"])


# Модель для запроса статистики
class StatisticsRequest(BaseModel):
    email: EmailStr


# Зависимость для получения сессии БД
def get_db():
    db = DatabaseConnection()
    if not db.is_connected:
        db.connect("sqlite:///woysa_database.db")

    session = db.get_session()
    try:
        yield session
    finally:
        session.close()


@router.get("/", response_model=List[Dict[str, Any]])
@cached(ttl=60)  # Кэшируем на 1 минуту
async def get_all_sallers(db: Session = Depends(get_db)):
    """
    Получение всех продавцов с кэшированием
    """
    logger.info("📋 Получение всех продавцов (с кэшированием)")

    try:
        sellers = db.query(Supplier).all()
        sellers_data = []

        for seller in sellers:
            seller_odt = ODTConverter.supplier_to_odt(seller)
            sellers_data.append(seller_odt.to_dict())

        logger.info(f"✅ Получено продавцов: {len(sellers_data)}")
        return sellers_data

    except Exception as e:
        logger.error(f"❌ Ошибка получения продавцов: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения данных")


@router.get("/{seller_id}/", response_model=Dict[str, Any])
@cached(ttl=120)  # Кэшируем на 2 минуты
async def get_saller_by_id(seller_id: int, db: Session = Depends(get_db)):
    """
    Получение продавца по ID с кэшированием
    """
    logger.info(f"🔍 Получение продавца с ID: {seller_id} (с кэшированием)")

    try:
        seller = db.query(Supplier).filter(Supplier.id == seller_id).first()

        if not seller:
            raise HTTPException(status_code=404, detail="Продавец не найден")

        seller_odt = ODTConverter.supplier_to_odt(seller)
        return seller_odt.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка получения продавца: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения данных")


@router.put("/{seller_id}/update", response_model=Dict[str, Any])
@invalidate_cache(pattern="cache:*")  # Очищаем кэш при обновлении
async def update_saller(seller_id: int, update_data: dict, db: Session = Depends(get_db)):
    """
    Обновление продавца по ID с инвалидацией кэша
    """
    logger.info(f"🔄 Обновление продавца с ID: {seller_id}")

    try:
        seller = db.query(Supplier).filter(Supplier.id == seller_id).first()

        if not seller:
            raise HTTPException(status_code=404, detail="Продавец не найден")

        allowed_fields = ['name', 'contact_person', 'email', 'phone', 'address', 'is_active']
        updated_fields = []

        for field, value in update_data.items():
            if field in allowed_fields and hasattr(seller, field):
                setattr(seller, field, value)
                updated_fields.append(field)

        db.commit()
        db.refresh(seller)

        seller_odt = ODTConverter.supplier_to_odt(seller)
        logger.info(f"✅ Продавец с ID {seller_id} обновлен. Измененные поля: {updated_fields}")
        return seller_odt.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Ошибка обновления продавца: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления данных")


@router.post("/statistics/")
async def request_statistics(
        request: StatisticsRequest,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db)
):
    """
    Запрос статистики с отправкой на email
    Соответствует требованию 02
    """
    logger.info(f"📊 Запрос статистики для email: {request.email}")

    try:
        # Запускаем фоновую задачу
        task = send_statistics_email.delay(request.email)

        return {
            "status": "success",
            "message": f"Запрос на генерацию отчета принят. Отчет будет отправлен на {request.email}",
            "task_id": task.id
        }

    except Exception as e:
        logger.error(f"❌ Ошибка запроса статистики: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обработки запроса")


@router.get("/cache/status/")
async def get_cache_status():
    """
    Получение статуса кэша
    """
    return {
        "redis_connected": cache.is_connected(),
        "cache_keys": len(cache.redis_client.keys("cache:*")) if cache.is_connected() else 0
    }


@router.delete("/cache/clear/")
async def clear_cache():
    """
    Очистка кэша
    """
    try:
        if cache.clear_pattern("cache:*"):
            return {"status": "success", "message": "Кэш очищен"}
        else:
            raise HTTPException(status_code=500, detail="Ошибка очистки кэша")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка очистки кэша: {e}")