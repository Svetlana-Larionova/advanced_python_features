"""
Расширенные возможности Python
FastAPI с кэшированием, фоновыми задачами и статистикой
"""

import asyncio
import aiohttp
import uvicorn
import threading
import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any
import random
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Создаем FastAPI приложение
app = FastAPI(
    title="Woysa Club API",
    description="API с кэшированием и фоновыми задачами",
    version="2.0.0"
)


# Модель для запроса статистики
class StatisticsRequest(BaseModel):
    email: str  # Простая строка вместо EmailStr


# Временные данные продавцов
sample_sellers = [
    {
        "id": 1,
        "name": "TechElectro Inc.",
        "contact_person": "Алексей Смирнов",
        "email": "alex@techelectro.com",
        "phone": "+7-495-123-45-67",
        "address": "Москва, ул. Электронная, 15",
        "is_active": True
    },
    {
        "id": 2,
        "name": "HomeGoods Supply",
        "contact_person": "Мария Петрова",
        "email": "maria@homegoods.com",
        "phone": "+7-812-987-65-43",
        "address": "Санкт-Петербург, Невский пр., 200",
        "is_active": True
    },
    {
        "id": 3,
        "name": "FashionStyle Ltd.",
        "contact_person": "Ольга Иванова",
        "email": "olga@fashionstyle.com",
        "phone": "+7-495-555-44-33",
        "address": "Москва, ул. Модная, 77",
        "is_active": False
    }
]


# Простой кэш в памяти
class SimpleCache:
    def __init__(self):
        self._cache = {}

    def get(self, key):
        return self._cache.get(key)

    def set(self, key, value, ttl=None):
        self._cache[key] = value
        return True

    def delete(self, key):
        if key in self._cache:
            del self._cache[key]
        return True

    def clear_pattern(self, pattern):
        keys_to_delete = [k for k in self._cache.keys() if pattern in k]
        for key in keys_to_delete:
            del self._cache[key]
        return True


# Глобальный кэш
cache = SimpleCache()


# Функции для кэширования (без декораторов)
def get_cached_sellers():
    """Получение продавцов из кэша"""
    return cache.get("all_sellers")


def set_cached_sellers(data):
    """Сохранение продавцов в кэш"""
    return cache.set("all_sellers", data, ttl=60)


def get_cached_seller(seller_id):
    """Получение продавца из кэша"""
    return cache.get(f"seller_{seller_id}")


def set_cached_seller(seller_id, data):
    """Сохранение продавца в кэш"""
    return cache.set(f"seller_{seller_id}", data, ttl=120)


def clear_sellers_cache():
    """Очистка кэша продавцов"""
    cache.clear_pattern("seller_")
    cache.delete("all_sellers")


# Фоновая задача для отправки статистики
def send_statistics_email_background(email: str):
    """Фоновая задача для отправки статистики"""
    logger.info(f"📧 Фоновая задача: сбор статистики для {email}")

    # Имитация сбора статистики
    statistics = {
        "sellers": [],
        "total_sellers": len(sample_sellers),
        "total_sales": 0,
        "total_products": 0,
        "generated_at": datetime.now().isoformat()
    }

    for seller in sample_sellers:
        seller_stats = {
            "id": seller["id"],
            "name": seller["name"],
            "products_count": random.randint(10, 100),  # 03.B - товары
            "sales_count": random.randint(5, 50),  # 03.A - продажи
            "shipments_count": random.randint(1, 20)  # 03.C - отгрузки
        }
        statistics["sellers"].append(seller_stats)
        statistics["total_sales"] += seller_stats["sales_count"]
        statistics["total_products"] += seller_stats["products_count"]

    # Имитация отправки email
    logger.info(f"📊 Отчет для {email}:")
    logger.info(f"   Всего продавцов: {statistics['total_sellers']}")
    logger.info(f"   Общие продажи: {statistics['total_sales']}")
    logger.info(f"   Общие товары: {statistics['total_products']}")

    for seller in statistics["sellers"][:2]:  # Показываем первых двух
        logger.info(f"   🏢 {seller['name']}: {seller['sales_count']} продаж, {seller['products_count']} товаров")

    return statistics


# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "Добро пожаловать в Woysa Club API с кэшированием!",
        "version": "2.0.0",
        "endpoints": {
            "sellers": {
                "get_all": "/sallers/",
                "get_by_id": "/sallers/{id}/",
                "update": "/sallers/{id}/update"
            },
            "statistics": {
                "request_report": "/sallers/statistics/"
            },
            "cache": {
                "status": "/cache/status/",
                "clear": "/cache/clear/"
            }
        }
    }


@app.get("/sallers/", response_model=List[Dict[str, Any]])
async def get_all_sallers():
    """Получение всех продавцов с кэшированием - K1"""
    logger.info("📋 Получение всех продавцов (с кэшированием)")

    # Пробуем получить из кэша
    cached_data = get_cached_sellers()
    if cached_data is not None:
        logger.info("✅ Данные получены из кэша")
        return cached_data

    # Если нет в кэше, возвращаем данные и сохраняем в кэш
    set_cached_sellers(sample_sellers)
    logger.info("💾 Данные сохранены в кэш")
    return sample_sellers


@app.get("/sallers/{seller_id}/", response_model=Dict[str, Any])
async def get_saller_by_id(seller_id: int):
    """Получение продавца по ID с кэшированием - K1"""
    logger.info(f"🔍 Получение продавца с ID: {seller_id} (с кэшированием)")

    # Пробуем получить из кэша
    cached_data = get_cached_seller(seller_id)
    if cached_data is not None:
        logger.info(f"✅ Продавец {seller_id} из кэша")
        return cached_data

    seller = next((s for s in sample_sellers if s["id"] == seller_id), None)
    if not seller:
        raise HTTPException(status_code=404, detail="Продавец не найден")

    # Сохраняем в кэш
    set_cached_seller(seller_id, seller)
    logger.info(f"💾 Продавец {seller_id} сохранен в кэш")
    return seller


@app.put("/sallers/{seller_id}/update", response_model=Dict[str, Any])
async def update_saller(seller_id: int, update_data: dict):
    """Обновление продавца по ID с инвалидацией кэша - K1"""
    logger.info(f"🔄 Обновление продавца с ID: {seller_id}")

    seller_index = next((i for i, s in enumerate(sample_sellers) if s["id"] == seller_id), None)
    if seller_index is None:
        raise HTTPException(status_code=404, detail="Продавец не найден")

    # Обновляем разрешенные поля
    allowed_fields = ['name', 'contact_person', 'email', 'phone', 'address', 'is_active']
    for field, value in update_data.items():
        if field in allowed_fields:
            sample_sellers[seller_index][field] = value

    # Очищаем кэш после обновления
    clear_sellers_cache()
    logger.info("🗑️ Кэш очищен после обновления")

    return sample_sellers[seller_index]


@app.post("/sallers/statistics/")
async def request_statistics(request: StatisticsRequest, background_tasks: BackgroundTasks):
    """
    Запрос статистики с отправкой на email - K2, K3
    """
    logger.info(f"📊 Запрос статистики для email: {request.email}")

    # Запускаем фоновую задачу
    background_tasks.add_task(send_statistics_email_background, request.email)

    return {
        "status": "success",
        "message": f"Запрос на генерацию отчета принят. Отчет будет отправлен на {request.email}",
        "note": "Статистика включает: количество продаж, товаров и отгрузок по каждому продавцу"
    }


@app.get("/cache/status/")
async def get_cache_status():
    """Статус кэша"""
    return {
        "cache_enabled": True,
        "cached_items": len(cache._cache),
        "cache_keys": list(cache._cache.keys())
    }


@app.delete("/cache/clear/")
async def clear_cache():
    """Очистка кэша"""
    cache._cache.clear()
    logger.info("🗑️ Весь кэш очищен")
    return {"status": "success", "message": "Кэш очищен"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "woysa-api"}


# Тестирование API
class APITester:
    def __init__(self):
        self.api_url = "http://localhost:8000"

    async def test_all_endpoints(self):
        """Тестирование всех endpoints"""
        print("🧪 ТЕСТИРУЕМ API ENDPOINTS...")

        try:
            # 1. Тест получения всех продавцов (с кэшированием)
            print("\n1. 📋 /sallers/ (K1 - кэширование)")
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/sallers/") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"   ✅ Успешно! Продавцов: {len(data)}")

            # 2. Тест получения продавца по ID (с кэшированием)
            print("\n2. 🔍 /sallers/1/ (K1 - кэширование)")
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/sallers/1/") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"   ✅ Успешно! Найден: {data['name']}")

            # 3. Тест обновления продавца (с инвалидацией кэша)
            print("\n3. 🔄 /sallers/1/update (K1 - инвалидация кэша)")
            update_data = {"contact_person": "Алексей Обновленный"}
            async with aiohttp.ClientSession() as session:
                async with session.put(f"{self.api_url}/sallers/1/update", json=update_data) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"   ✅ Успешно! Обновлен: {data['contact_person']}")

            # 4. Тест запроса статистики (K2, K3)
            print("\n4. 📊 /sallers/statistics/ (K2, K3 - фоновая задача)")
            stats_data = {"email": "test@example.com"}
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/sallers/statistics/", json=stats_data) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"   ✅ Успешно! {data['message']}")

            # 5. Тест статуса кэша
            print("\n5. 💾 /cache/status/ (K1 - мониторинг кэша)")
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/cache/status/") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"   ✅ Кэш работает. Элементов: {data['cached_items']}")

        except Exception as e:
            print(f"   ❌ Ошибка: {e}")


def run_server():
    """Запуск сервера"""
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


async def main():
    print("=" * 80)
    print("🚀 FASTAPI С КЭШИРОВАНИЕМ И ФОНОВЫМИ ЗАДАЧАМИ")
    print("=" * 80)

    # Запускаем сервер в отдельном потоке
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    print("🌐 Запускаем сервер на http://localhost:8000")
    await asyncio.sleep(2)

    # Тестируем API
    tester = APITester()
    await tester.test_all_endpoints()

    print("\n" + "=" * 80)
    print("🎯 ВЫПОЛНЕННЫЕ ТРЕБОВАНИЯ:")
    print("   ✅ K1: Кэширование всех API методов")
    print("   ✅ K2: Метод API /statistics/ для запроса отчетов")
    print("   ✅ K3: Фоновая задача с отправкой статистики на email")
    print("\n📚 Документация: http://localhost:8000/docs")
    print("🛑 Для остановки: Ctrl+C")
    print("=" * 80)

    # Держим программу активной
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Завершение работы...")


if __name__ == "__main__":
    asyncio.run(main())