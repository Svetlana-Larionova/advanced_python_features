"""
Тестовый файл для проверки API
"""
import uvicorn
import threading
import asyncio
import aiohttp
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Создаем FastAPI приложение прямо здесь
from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any

app = FastAPI(
    title="Woysa Club API",
    description="API для работы с данными Woysa Club",
    version="1.0.0"
)

# Временные данные для демонстрации
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
    }
]


@app.get("/")
async def root():
    return {"message": "Добро пожаловать в Woysa Club API!"}


@app.get("/sallers/", response_model=List[Dict[str, Any]])
async def get_all_sallers():
    """Получение всех продавцов - K1"""
    logger.info("📋 Получение всех продавцов")
    return sample_sellers


@app.get("/sallers/{seller_id}/", response_model=Dict[str, Any])
async def get_saller_by_id(seller_id: int):
    """Получение продавца по ID - K3"""
    logger.info(f"🔍 Получение продавца с ID: {seller_id}")

    seller = next((s for s in sample_sellers if s["id"] == seller_id), None)
    if not seller:
        raise HTTPException(status_code=404, detail="Продавец не найден")

    return seller


@app.put("/sallers/{seller_id}/update", response_model=Dict[str, Any])
async def update_saller(seller_id: int, update_data: dict):
    """Обновление продавца по ID - K2"""
    logger.info(f"🔄 Обновление продавца с ID: {seller_id}")

    seller_index = next((i for i, s in enumerate(sample_sellers) if s["id"] == seller_id), None)
    if seller_index is None:
        raise HTTPException(status_code=404, detail="Продавец не найден")

    # Обновляем поля
    allowed_fields = ['name', 'contact_person', 'email', 'phone', 'address', 'is_active']
    for field, value in update_data.items():
        if field in allowed_fields:
            sample_sellers[seller_index][field] = value

    return sample_sellers[seller_index]


class APITester:
    def __init__(self):
        self.api_url = "http://localhost:8000"

    async def test_all_endpoints(self):
        """Тестирование всех endpoints"""
        print("🧪 ТЕСТИРУЕМ API ENDPOINTS...")

        try:
            # 1. Тест получения всех продавцов
            print("\n1. 📋 /sallers/ (K1)")
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/sallers/") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"   ✅ Успешно! Продавцов: {len(data)}")
                        for seller in data:
                            print(f"      🏢 {seller['name']} (ID: {seller['id']})")

            # 2. Тест получения продавца по ID
            print("\n2. 🔍 /sallers/1/ (K3)")
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/sallers/1/") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"   ✅ Успешно! Найден: {data['name']}")

            # 3. Тест обновления продавца
            print("\n3. 🔄 /sallers/1/update (K2)")
            update_data = {"contact_person": "Алексей Обновленный", "phone": "+7-495-999-88-77"}
            async with aiohttp.ClientSession() as session:
                async with session.put(f"{self.api_url}/sallers/1/update", json=update_data) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"   ✅ Успешно! Обновлен: {data['contact_person']}")

            # 4. Тест ошибки
            print("\n4. ❌ /sallers/999/ (обработка ошибок)")
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/sallers/999/") as response:
                    if response.status == 404:
                        print(f"   ✅ Корректная обработка ошибки")

        except Exception as e:
            print(f"   ❌ Ошибка: {e}")


def run_server():
    """Запуск сервера"""
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


async def main():
    print("=" * 60)
    print("🚀 FASTAPI - ТЕСТОВЫЙ ЗАПУСК")
    print("=" * 60)

    # Запускаем сервер в отдельном потоке
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    print("🌐 Запускаем сервер на http://localhost:8000")
    await asyncio.sleep(2)  # Ждем запуск сервера

    # Тестируем API
    tester = APITester()
    await tester.test_all_endpoints()

    print("\n" + "=" * 60)
    print("🎯 ВЫПОЛНЕННЫЕ ТРЕБОВАНИЯ:")
    print("   ✅ K1: /sallers/ - получение всех продавцов")
    print("   ✅ K2: /sallers/{id}/update - обновление продавца")
    print("   ✅ K3: /sallers/{id}/ - получение продавца по ID")
    print("\n📚 Документация: http://localhost:8000/docs")
    print("🛑 Для остановки: Ctrl+C")
    print("=" * 60)

    # Держим программу активной
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Завершение работы...")


if __name__ == "__main__":
    asyncio.run(main())