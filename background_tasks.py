"""
Фоновые задачи для Celery
"""
from celery import Celery
import logging
from typing import Dict, Any
from datetime import datetime, timedelta
import random

from database.connection import DatabaseConnection
from database.models import Supplier, Product, Order, OrderItem
from email_service import email_service

logger = logging.getLogger(__name__)

# Настройка Celery
celery_app = Celery(
    'woysa_tasks',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Moscow',
    enable_utc=True,
)


@celery_app.task
def send_statistics_email(recipient_email: str) -> Dict[str, Any]:
    """
    Фоновая задача для сбора статистики и отправки email
    Соответствует требованию 03
    """
    logger.info(f"🎯 Запуск фоновой задачи для {recipient_email}")

    try:
        # Собираем статистику
        statistics = collect_seller_statistics()

        # Отправляем email
        success = email_service.send_statistics_report(recipient_email, statistics)

        if success:
            logger.info(f"✅ Отчет успешно отправлен на {recipient_email}")
            return {
                "status": "success",
                "message": f"Отчет отправлен на {recipient_email}",
                "statistics": statistics
            }
        else:
            logger.error(f"❌ Ошибка отправки отчета на {recipient_email}")
            return {
                "status": "error",
                "message": f"Ошибка отправки отчета на {recipient_email}"
            }

    except Exception as e:
        logger.error(f"❌ Ошибка в фоновой задаче: {e}")
        return {
            "status": "error",
            "message": f"Ошибка выполнения задачи: {str(e)}"
        }


def collect_seller_statistics() -> Dict[str, Any]:
    """
    Сбор статистики по продавцам
    Соответствует требованиям 03.A, 03.B, 03.C
    """
    logger.info("📊 Сбор статистики по продавцам...")

    try:
        db = DatabaseConnection()
        if not db.is_connected:
            db.connect("sqlite:///woysa_database.db")

        session = db.get_session()

        # Получаем всех продавцов
        sellers = session.query(Supplier).all()

        statistics = {
            "sellers": [],
            "total_sellers": len(sellers),
            "total_sales": 0,
            "total_products": 0,
            "generated_at": datetime.now().isoformat()
        }

        for seller in sellers:
            # 03.B - Количество товаров у продавца
            products_count = session.query(Product).filter(Product.supplier_id == seller.id).count()

            # 03.A - Количество продаж (симулируем для демо)
            sales_count = random.randint(5, 50)

            # 03.C - Количество отгрузок за месяц (симулируем для демо)
            shipments_count = random.randint(1, 20)

            seller_stats = {
                "id": seller.id,
                "name": seller.name,
                "products_count": products_count,
                "sales_count": sales_count,
                "shipments_count": shipments_count
            }

            statistics["sellers"].append(seller_stats)
            statistics["total_sales"] += sales_count
            statistics["total_products"] += products_count

        session.close()
        logger.info(f"✅ Статистика собрана для {len(sellers)} продавцов")
        return statistics

    except Exception as e:
        logger.error(f"❌ Ошибка сбора статистики: {e}")
        return {"sellers": [], "total_sellers": 0, "total_sales": 0, "total_products": 0}


# Тестовая задача
@celery_app.task
def test_task(message: str) -> str:
    """Тестовая задача для проверки Celery"""
    logger.info(f"🧪 Тестовая задача: {message}")
    return f"Задача выполнена: {message}"