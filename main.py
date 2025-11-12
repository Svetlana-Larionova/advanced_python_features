"""
Расширенные возможности Python
FastAPI - создание REST API
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
import uvicorn
import threading

# Импорты для работы с БД
from database.connection import DatabaseConnection
from database.base import Base
from database.models import Supplier, Product, Order, OrderItem
from database.odt import ODTConverter, OrderODT, ProductODT, SupplierODT

# Импорты для API
from api.main import app as fastapi_app

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class APIDemo:
    """Демонстрация работы API"""

    def __init__(self):
        self.db = DatabaseConnection()
        self.api_url = "http://localhost:8000"

    def setup_database(self):
        """Настройка базы данных с тестовыми данными"""
        connection_string = "sqlite:///woysa_database.db"

        if self.db.connect(connection_string, echo=False):
            self.db.create_tables(Base)
            self._create_sample_data()
            return True
        return False

    def _create_sample_data(self):
        """Создание тестовых данных продавцов"""
        try:
            session = self.db.get_session()

            # Проверяем, есть ли уже данные
            existing_sellers = session.query(Supplier).count()
            if existing_sellers > 0:
                logger.info("✅ Тестовые данные уже существуют")
                return

            # Создаем тестовых продавцов
            sellers_data = [
                {
                    "name": "TechElectro Inc.",
                    "contact_person": "Алексей Смирнов",
                    "email": "alex@techelectro.com",
                    "phone": "+7-495-123-45-67",
                    "address": "Москва, ул. Электронная, 15",
                    "is_active": True
                },
                {
                    "name": "HomeGoods Supply",
                    "contact_person": "Мария Петрова",
                    "email": "maria@homegoods.com",
                    "phone": "+7-812-987-65-43",
                    "address": "Санкт-Петербург, Невский пр., 200",
                    "is_active": True
                },
                {
                    "name": "FashionStyle Ltd.",
                    "contact_person": "Ольга Иванова",
                    "email": "olga@fashionstyle.com",
                    "phone": "+7-495-555-44-33",
                    "address": "Москва, ул. Модная, 77",
                    "is_active": False
                }
            ]

            for data in sellers_data:
                seller = Supplier(**data)
                session.add(seller)

            session.commit()
            logger.info("✅ Тестовые данные продавцов созданы")

        except Exception as e:
            logger.error(f"❌ Ошибка создания тестовых данных: {e}")
            session.rollback()
        finally:
            session.close()

    async def test_api_endpoints(self):
        """Тестирование API endpoints"""
        logger.info("🧪 Тестирование API endpoints...")

        try:
            # 1. Тестируем получение всех продавцов
            print(f"\n1. 📋 ТЕСТ /sallers/ (K1)")
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/sallers/") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"   ✅ Успешно! Получено продавцов: {len(data)}")
                        for seller in data[:2]:  # Показываем первых двух
                            print(f"      🏢 {seller['name']} (ID: {seller['id']})")
                    else:
                        print(f"   ❌ Ошибка: {response.status}")

            # 2. Тестируем получение продавца по ID
            print(f"\n2. 🔍 ТЕСТ /sallers/1/ (K3)")
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/sallers/1/") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"   ✅ Успешно! Найден продавец:")
                        print(f"      🆔 ID: {data['id']}")
                        print(f"      🏢 Название: {data['name']}")
                        print(f"      👤 Контакт: {data['contact_person']}")
                        print(f"      📧 Email: {data['email']}")
                    else:
                        print(f"   ❌ Ошибка: {response.status}")

            # 3. Тестируем обновление продавца
            print(f"\n3. 🔄 ТЕСТ /sallers/1/update (K2)")
            update_data = {
                "contact_person": "Алексей Обновленный",
                "phone": "+7-495-999-88-77"
            }
            async with aiohttp.ClientSession() as session:
                async with session.put(
                        f"{self.api_url}/sallers/1/update",
                        json=update_data
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"   ✅ Успешно! Продавец обновлен:")
                        print(f"      👤 Новый контакт: {data['contact_person']}")
                        print(f"      📞 Новый телефон: {data['phone']}")
                    else:
                        print(f"   ❌ Ошибка: {response.status}")

            # 4. Тестируем несуществующий ID
            print(f"\n4. ❌ ТЕСТ ОШИБКИ /sallers/999/")
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/sallers/999/") as response:
                    if response.status == 404:
                        print(f"   ✅ Корректная обработка ошибки: продавец не найден")
                    else:
                        print(f"   ❌ Неожиданный статус: {response.status}")

        except Exception as e:
            logger.error(f"❌ Ошибка тестирования API: {e}")
            print(f"   ❌ Ошибка: {e}")


def run_fastapi():
    """Запуск FastAPI сервера в отдельном потоке"""
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000, log_level="info")


async def main():
    print("=" * 80)
    print("🚀 FASTAPI - СОЗДАНИЕ REST API")
    print("=" * 80)

    # Инициализация демо
    api_demo = APIDemo()

    print("\n1. 🗄️  ПОДГОТОВКА БАЗЫ ДАННЫХ:")
    if api_demo.setup_database():
        print("   ✅ База данных готова")
    else:
        print("   ❌ Ошибка подготовки базы данных")
        return

    print("\n2. 🌐 ЗАПУСК FASTAPI СЕРВЕРА:")
    print("   🚀 Запускаем сервер на http://localhost:8000")

    # Запускаем FastAPI в отдельном потоке
    api_thread = threading.Thread(target=run_fastapi, daemon=True)
    api_thread.start()

    # Даем серверу время на запуск
    print("   ⏳ Ожидаем запуск сервера...")
    await asyncio.sleep(3)

    print("\n3. 🧪 ТЕСТИРОВАНИЕ API ENDPOINTS:")
    await api_demo.test_api_endpoints()

    print("\n" + "=" * 80)
    print("🎯 ВЫПОЛНЕННЫЕ ТРЕБОВАНИЯ:")
    print("   ✅ K1: Реализован метод API /sallers и вывод данных на экран")
    print("   ✅ K2: Реализован метод API /sallers/{id}/update и вывод данных на экран")
    print("   ✅ K3: Реализован метод API /sallers/{id}/ и вывод данных на экран")
    print("\n🌐 API доступно по адресу: http://localhost:8000")
    print("📚 Документация: http://localhost:8000/docs")
    print("=" * 80)

    # Держим программу активной для работы сервера
    print("\n🛑 Для остановки нажмите Ctrl+C")
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Завершение работы...")


if __name__ == "__main__":
    asyncio.run(main())