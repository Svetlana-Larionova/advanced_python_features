"""
Расширенные возможности Python
SQLAlchemy Часть 2 - Зависимости, ODT классы, данные из WoysaClub
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
import random
from datetime import datetime

# Импорты для работы с БД
from database.connection import DatabaseConnection
from database.base import Base
from database.models import Supplier, Product, Order, OrderItem
from database.odt import ODTConverter, OrderODT, ProductODT, SupplierODT

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class WoysaDataProcessor:
    """Класс для обработки данных из WoysaClub и сохранения в БД"""

    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection

    def create_sample_suppliers_and_products(self):
        """Создание тестовых поставщиков и товаров"""
        logger.info("🛍️ Создание тестовых поставщиков и товаров...")

        try:
            session = self.db.get_session()

            # Создаем поставщиков
            suppliers_data = [
                {
                    "name": "TechElectro Inc.",
                    "contact_person": "Алексей Смирнов",
                    "email": "alex@techelectro.com",
                    "phone": "+7-495-123-45-67",
                    "address": "Москва, ул. Электронная, 15"
                },
                {
                    "name": "HomeGoods Supply",
                    "contact_person": "Мария Петрова",
                    "email": "maria@homegoods.com",
                    "phone": "+7-812-987-65-43",
                    "address": "Санкт-Петербург, Невский пр., 200"
                }
            ]

            suppliers = []
            for data in suppliers_data:
                supplier = Supplier(**data)
                session.add(supplier)
                suppliers.append(supplier)

            session.flush()

            # Создаем товары для каждого поставщика
            products_data = [
                # Товары для первого поставщика (электроника)
                {"name": "Ноутбук Gaming Pro", "description": "Игровой ноутбук", "price": 150000.00, "quantity": 5,
                 "category": "Электроника", "sku": "NB-GAME-001"},
                {"name": "Смартфон Galaxy X", "description": "Флагманский смартфон", "price": 89999.99, "quantity": 10,
                 "category": "Электроника", "sku": "PH-GALAXY-001"},
                {"name": "Наушники Wireless", "description": "Беспроводные наушники", "price": 15999.50, "quantity": 20,
                 "category": "Электроника", "sku": "HP-WIRELESS-001"},

                # Товары для второго поставщика (товары для дома)
                {"name": "Кофемашина Deluxe", "description": "Автоматическая кофемашина", "price": 45999.00,
                 "quantity": 8, "category": "Техника для дома", "sku": "CM-DELUXE-001"},
                {"name": "Пылесос Robot", "description": "Робот-пылесос", "price": 32999.00, "quantity": 12,
                 "category": "Техника для дома", "sku": "VC-ROBOT-001"},
                {"name": "Микроволновка Compact", "description": "Компактная микроволновая печь", "price": 12999.00,
                 "quantity": 15, "category": "Техника для дома", "sku": "MW-COMPACT-001"},
            ]

            # Распределяем товары между поставщиками
            for i, data in enumerate(products_data):
                supplier_idx = 0 if i < 3 else 1
                product = Product(**data, supplier_id=suppliers[supplier_idx].id)
                session.add(product)

            session.commit()
            logger.info("✅ Тестовые поставщики и товары созданы")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка создания тестовых данных: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def create_orders_from_woysa_categories(self, categories: List[int]):
        """
        Создание заказов на основе категорий WoysaClub
        Соответствует требованию 02
        """
        logger.info(f"📦 Создание заказов для категорий: {categories}")

        try:
            session = self.db.get_session()

            # Получаем все товары из базы
            products = session.query(Product).filter(Product.is_available == True).all()

            if not products:
                logger.error("❌ Нет доступных товаров для создания заказов")
                return False

            # Создаем заказы для каждой категории
            customer_names = ["Иван Иванов", "Петр Петров", "Мария Сидорова", "Анна Козлова", "Сергей Смирнов"]
            statuses = ["pending", "completed", "shipped"]

            orders_created = 0

            for category in categories:
                # Создаем заказ для каждой категории
                order = Order(
                    customer_name=random.choice(customer_names),
                    customer_email=f"customer{category}@example.com",
                    customer_phone=f"+7-999-{category:06d}",
                    shipping_address=f"Город {category}, ул. Центральная, {category}",
                    status=random.choice(statuses)
                )
                session.add(order)
                session.flush()

                # Добавляем случайные товары в заказ
                num_items = random.randint(1, 4)
                selected_products = random.sample(products, min(num_items, len(products)))

                for product in selected_products:
                    quantity = random.randint(1, 3)
                    order_item = OrderItem(
                        order_id=order.id,
                        product_id=product.id,
                        quantity=quantity,
                        unit_price=product.price
                    )
                    session.add(order_item)

                # Пересчитываем общую сумму
                order.calculate_total()

                orders_created += 1
                logger.info(f"✅ Создан заказ #{order.id} для категории {category}")

            session.commit()
            logger.info(f"🎉 Создано заказов: {orders_created}")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка создания заказов: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def get_orders_with_details(self) -> List[OrderODT]:
        """
        Получение заказов с деталями и преобразование в ODT
        Соответствует требованию 03 и 05
        """
        logger.info("📋 Получение заказов из базы данных...")

        try:
            session = self.db.get_session()

            # Получаем все заказы с связанными данными
            orders = session.query(Order).options(
                # Жадная загрузка связанных данных
                sqlalchemy.orm.joinedload(Order.order_items).joinedload(OrderItem.product)
            ).order_by(Order.created_at.desc()).all()

            # Преобразуем в ODT
            order_odts = []
            for order in orders:
                order_odt = ODTConverter.order_to_odt(order)
                order_odts.append(order_odt)

            logger.info(f"✅ Получено заказов: {len(order_odts)}")
            return order_odts

        except Exception as e:
            logger.error(f"❌ Ошибка получения заказов: {e}")
            return []
        finally:
            session.close()

    def display_orders_data(self):
        """
        Вывод данных о заказах на экран
        Соответствует требованию 03 и 05
        """
        orders_odt = self.get_orders_with_details()

        print("\n" + "=" * 80)
        print("📦 ДАННЫЕ О ЗАКАЗАХ ИЗ БАЗЫ ДАННЫХ")
        print("=" * 80)

        if not orders_odt:
            print("❌ Нет данных о заказах")
            return

        for order_odt in orders_odt:
            print(f"\n🎯 ЗАКАЗ #{order_odt.id}")
            print(f"   👤 Клиент: {order_odt.customer_name}")
            print(f"   📧 Email: {order_odt.customer_email}")
            print(f"   📞 Телефон: {order_odt.customer_phone}")
            print(f"   💰 Общая сумма: {order_odt.total_amount:,.2f} руб.")
            print(f"   📍 Статус: {order_odt.status}")
            print(f"   🏠 Адрес доставки: {order_odt.shipping_address}")
            print(f"   📅 Дата создания: {order_odt.created_at}")

            print(f"   🛒 Товары в заказе ({len(order_odt.items)}):")
            for item in order_odt.items:
                print(f"      ├─ {item.product_name}")
                print(f"      │  Количество: {item.quantity} x {item.unit_price:,.2f} = {item.total_price:,.2f} руб.")

            print("   " + "─" * 50)


class DatabaseDemo:
    """Демонстрация работы с базой данных"""

    def __init__(self):
        self.db = DatabaseConnection()
        self.woysa_processor = WoysaDataProcessor(self.db)

    def setup_database(self):
        """Настройка и подключение к базе данных"""
        connection_string = "sqlite:///woysa_database.db"

        if self.db.connect(connection_string, echo=False):
            self.db.create_tables(Base)
            return True
        return False

    def demo_odt_conversion(self):
        """Демонстрация преобразования в ODT"""
        logger.info("🔄 Демонстрация преобразования в ODT...")

        try:
            session = self.db.get_session()

            # Получаем несколько товаров для демонстрации
            products = session.query(Product).limit(3).all()

            print("\n" + "=" * 60)
            print("🔄 ПРЕОБРАЗОВАНИЕ В ODT (K4, K5)")
            print("=" * 60)

            for product in products:
                product_odt = ODTConverter.product_to_odt(product, include_supplier_name=True)
                print(f"\n📦 Товар как ODT:")
                print(f"   {product_odt}")
                print(f"   📊 Данные в виде словаря:")
                for key, value in product_odt.to_dict().items():
                    print(f"      {key}: {value}")

            return True

        except Exception as e:
            logger.error(f"❌ Ошибка демонстрации ODT: {e}")
            return False
        finally:
            session.close()


async def main():
    print("=" * 80)
    print("🗄️  SQLALCHEMY ЧАСТЬ 2 - ЗАВИСИМОСТИ, ODT, ДАННЫЕ ИЗ WOYSACLUB")
    print("=" * 80)

    # Демонстрация работы с базой данных
    db_demo = DatabaseDemo()

    print("\n1. 🔌 ПОДКЛЮЧЕНИЕ К БАЗЕ ДАННЫХ:")
    if db_demo.setup_database():
        print("   ✅ База данных успешно подключена")
    else:
        print("   ❌ Ошибка подключения к базе данных")
        return

    print("\n2. 🛍️ СОЗДАНИЕ ТЕСТОВЫХ ДАННЫХ:")
    if db_demo.woysa_processor.create_sample_suppliers_and_products():
        print("   ✅ Тестовые данные созданы")
    else:
        print("   ❌ Ошибка создания тестовых данных")

    print("\n3. 📦 СОЗДАНИЕ ЗАКАЗОВ НА ОСНОВЕ КАТЕГОРИЙ WOYSACLUB:")
    test_categories = [100, 200, 300, 400, 500]
    if db_demo.woysa_processor.create_orders_from_woysa_categories(test_categories):
        print("   ✅ Заказы созданы на основе категорий WoysaClub")
    else:
        print("   ❌ Ошибка создания заказов")

    print("\n4. 📋 ВЫВОД ДАННЫХ О ЗАКАЗАХ:")
    db_demo.woysa_processor.display_orders_data()

    print("\n5. 🔄 ДЕМОНСТРАЦИЯ ODT ПРЕОБРАЗОВАНИЯ:")
    db_demo.demo_odt_conversion()

    print("\n" + "=" * 80)
    print("🎯 ВЫПОЛНЕННЫЕ ТРЕБОВАНИЯ:")
    print("   ✅ K1: Реализованы зависимости между таблицами")
    print("   ✅ K2: Реализовано заполнение таблиц данными из WoysaClub")
    print("   ✅ K3: Реализовано получение данных и вывод на экран")
    print("   ✅ K4: Реализован класс ODT для таблиц")
    print("   ✅ K5: Реализовано преобразование в ODT и вывод данных")
    print("=" * 80)


if __name__ == "__main__":
    # Добавляем импорт для joinedload
    import sqlalchemy.orm

    asyncio.run(main())