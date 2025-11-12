"""
Маршруты для работы с продавцами (sellers)
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from sqlalchemy.orm import Session
import logging

from database.connection import DatabaseConnection
from database.models import Supplier
from database.odt import SupplierODT, ODTConverter

logger = logging.getLogger(__name__)

# Создаем роутер
router = APIRouter(prefix="/sallers", tags=["sallers"])


# Зависимость для получения сессии БД
def get_db():
    db = DatabaseConnection()
    if not db.is_connected:
        # Подключаемся к БД если еще не подключены
        db.connect("sqlite:///woysa_database.db")

    session = db.get_session()
    try:
        yield session
    finally:
        session.close()


@router.get("/", response_model=List[Dict[str, Any]])
async def get_all_sallers(db: Session = Depends(get_db)):
    """
    Получение всех продавцов
    Соответствует требованию 01.A - /sallers
    """
    logger.info("📋 Получение всех продавцов")

    try:
        # Получаем всех продавцов из базы
        sellers = db.query(Supplier).all()

        # Преобразуем в ODT и затем в словарь
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
async def get_saller_by_id(seller_id: int, db: Session = Depends(get_db)):
    """
    Получение продавца по ID
    Соответствует требованию 01.C - /sallers/{id}/
    """
    logger.info(f"🔍 Получение продавца с ID: {seller_id}")

    try:
        # Ищем продавца в базе
        seller = db.query(Supplier).filter(Supplier.id == seller_id).first()

        if not seller:
            logger.warning(f"❌ Продавец с ID {seller_id} не найден")
            raise HTTPException(status_code=404, detail="Продавец не найден")

        # Преобразуем в ODT и затем в словарь
        seller_odt = ODTConverter.supplier_to_odt(seller)

        logger.info(f"✅ Продавец с ID {seller_id} найден: {seller.name}")
        return seller_odt.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка получения продавца: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения данных")


@router.put("/{seller_id}/update", response_model=Dict[str, Any])
async def update_saller(seller_id: int, update_data: dict, db: Session = Depends(get_db)):
    """
    Обновление продавца по ID
    Соответствует требованию 01.B - /sallers/{id}/update
    """
    logger.info(f"🔄 Обновление продавца с ID: {seller_id}")

    try:
        # Ищем продавца в базе
        seller = db.query(Supplier).filter(Supplier.id == seller_id).first()

        if not seller:
            logger.warning(f"❌ Продавец с ID {seller_id} не найден")
            raise HTTPException(status_code=404, detail="Продавец не найден")

        # Разрешенные поля для обновления
        allowed_fields = ['name', 'contact_person', 'email', 'phone', 'address', 'is_active']

        # Обновляем только разрешенные поля
        updated_fields = []
        for field, value in update_data.items():
            if field in allowed_fields and hasattr(seller, field):
                setattr(seller, field, value)
                updated_fields.append(field)

        # Сохраняем изменения
        db.commit()

        # Обновляем объект для получения актуальных данных
        db.refresh(seller)

        # Преобразуем в ODT и затем в словарь
        seller_odt = ODTConverter.supplier_to_odt(seller)

        logger.info(f"✅ Продавец с ID {seller_id} обновлен. Измененные поля: {updated_fields}")
        return seller_odt.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Ошибка обновления продавца: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления данных")