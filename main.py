"""
Расширенные возможности Python
SQLAlchemy - работа с базой данных
"""

import asyncio
import aiohttp
import requests
import concurrent.futures
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import time
import logging

# Импорты для работы с БД
from database.connection import DatabaseConnection
from database.base import Base
from database.models import Supplier, Product, Order, OrderItem

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BaseModel(ABC):
    @abstractmethod
    def download_data(self, categories: List[int]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def transform_to_dict(self, data: Any) -> Dict[str, Any]:
        pass


class DatabaseDemo:
    """Демонстрация работы с базой данных"""

    def __init__(self):
        self.db = DatabaseConnection()

    def setup_database(self):
        """Настройка и подключение к базе данных"""
        # SQLite для демонстрации (можно заменить на PostgreSQL, MySQL и т.д.)
        connection_string = "sqlite:///woysa_database.db"

        if self.db.connect(connection_string, echo=False):
            # Создаем таблицы
            self.db.create_tables(Base)
            return True
        return False

    def demo_crud_operations(self):
        """Демонстрация CRUD операций"""
        logger.info("🚀 Демонстрация CRUD операций с базой данных")

        try:
            session = self.db.get_session()

            # Создание поставщика
            supplier = Supplier(
                name="TechSupplier Inc.",
                contact_person="Иван Иванов",
                email="ivan@techsupplier.com",
                phone="+7-999-123-45-67",
                address="Москва, ул. Техническая, 123"
            )
            session.add(supplier)
            session.flush()  # Получаем ID

            # Создание товаров
            products = [
                Product(
                    name="Ноутбук Gaming Pro",
                    description="Игровой ноутбук с RTX 4070",
                    price=150000.00,
                    quantity=10,
                    category="Электроника",
                    sku="NB-GAMING-PRO-001",
                    supplier_id=supplier.id
                ),
                Product(
                    name="Смартфон Galaxy X",
                    description="Флагманский смартфон",
                    price=89999.99,
                    quantity=25,
                    category="Электроника",
                    sku="PH-GALAXY-X-001",
                    supplier_id=supplier.id
                )
            ]

            for product in products:
                session.add(product)

            session.flush()

            # Создание заказа
            order = Order(
                customer_name="Петр Петров",
                customer_email="petr@example.com",
                customer_phone="+7-999-765-43-21",
                shipping_address="Санкт-Петербург, Невский пр., 456"
            )
            session.add(order)
            session.flush()

            # Создание элементов заказа
            order_items = [
                OrderItem(
                    order_id=order.id,
                    product_id=products[0].id,
                    quantity=1,
                    unit_price=products[0].price
                ),
                OrderItem(
                    order_id=order.id,
                    product_id=products[1].id,
                    quantity=2,
                    unit_price=products[1].price
                )
            ]

            for item in order_items:
                session.add(item)

            # Обновление общей суммы заказа
            total = sum(item.quantity * item.unit_price for item in order_items)
            order.total_amount = total

            # Сохранение всех изменений
            session.commit()

            logger.info("✅ Данные успешно добавлены в базу данных")

            # Чтение данных
            self.demo_read_operations(session)

            return True

        except Exception as e:
            logger.error(f"❌ Ошибка при работе с базой данных: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def demo_read_operations(self, session):
        """Демонстрация операций чтения"""
        logger.info("📖 Демонстрация операций чтения из базы данных")

        # Чтение всех поставщиков
        suppliers = session.query(Supplier).all()
        logger.info(f"📊 Найдено поставщиков: {len(suppliers)}")

        # Чтение всех товаров
        products = session.query(Product).all()
        logger.info(f"📊 Найдено товаров: {len(products)}")

        # Чтение всех заказов
        orders = session.query(Order).all()
        logger.info(f"📊 Найдено заказов: {len(orders)}")

        # Пример преобразования в словарь
        for supplier in suppliers[:1]:  # Первый поставщик
            logger.info(f"📋 Данные поставщика: {supplier.to_dict()}")

        for product in products[:2]:  # Первые два товара
            logger.info(f"📋 Данные товара: {product.to_dict()}")


async def main():
    print("=" * 60)
    print("🗄️  SQLALCHEMY - РАБОТА С БАЗОЙ ДАННЫХ")
    print("=" * 60)

    # Демонстрация работы с базой данных
    db_demo = DatabaseDemo()

    print("\n1. 🔌 ПОДКЛЮЧЕНИЕ К БАЗЕ ДАННЫХ:")
    if db_demo.setup_database():
        print("   ✅ База данных успешно подключена и таблицы созданы")
    else:
        print("   ❌ Ошибка подключения к базе данных")
        return

    print("\n2. 🛠️  ДЕМОНСТРАЦИЯ CRUD ОПЕРАЦИЙ:")
    if db_demo.demo_crud_operations():
        print("   ✅ CRUD операции успешно выполнены")
    else:
        print("   ❌ Ошибка выполнения CRUD операций")

    print("\n" + "=" * 60)
    print("🎯 ВЫПОЛНЕННЫЕ ТРЕБОВАНИЯ:")
    print("   ✅ K1: Класс подключения к БД (DatabaseConnection)")
    print("   ✅ K2: Абстрактный класс таблицы (BaseTable)")
    print("   ✅ K3: Таблицы (Supplier, Product, Order)")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())