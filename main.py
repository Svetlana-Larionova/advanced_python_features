"""
Расширенные возможности Python
Асинхронное программирование, многопоточность, пакетная обработка
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
from dataclasses import dataclass

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class BatchConfig:
    """Конфигурация для пакетной обработки"""
    batch_size: int = 5
    max_workers: int = 3
    timeout: int = 10


class BaseModel(ABC):

    @abstractmethod
    def download_data(self, categories: List[int]) -> Dict[str, Any]:
        """Синхронное получение данных"""
        pass

    @abstractmethod
    def transform_to_dict(self, data: Any) -> Dict[str, Any]:
        """Преобразование данных в словарь"""
        pass


class AdvancedWoysaLoader(BaseModel):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.base_url = 'https://analitika.woysa.club/images/panel/json/download/niches.php'
        self.batch_config = BatchConfig()
        logger.info("🚀 AdvancedWoysaLoader инициализирован")

    def download_data(self, categories: List[int]) -> Dict[str, Any]:
        """Синхронная загрузка данных"""
        logger.info(f"📥 Синхронная загрузка {len(categories)} категорий")
        results = {}

        for category in categories:
            try:
                url = self._build_url(category)
                response = requests.get(url, timeout=self.batch_config.timeout)

                # Проверяем Content-Type перед парсингом JSON
                content_type = response.headers.get('content-type', '')
                if 'application/json' in content_type:
                    results[str(category)] = response.json()
                    logger.info(f"✅ Загружена категория {category}")
                else:
                    # Если не JSON, сохраняем текст ответа
                    results[str(category)] = {
                        "content_type": content_type,
                        "text_preview": response.text[:100] + "..." if len(response.text) > 100 else response.text,
                        "status_code": response.status_code
                    }
                    logger.info(f"⚠️  Категория {category}: получен {content_type}")

            except Exception as e:
                logger.error(f"❌ Ошибка категории {category}: {e}")
                results[str(category)] = {"error": str(e)}

        return results

    async def download_data_async(self, categories: List[int]) -> Tuple[Dict[str, Any], float]:
        """Асинхронная загрузка данных с возвратом времени выполнения"""
        logger.info(f"⚡ Асинхронная загрузка {len(categories)} категорий")
        start_time = time.time()
        results = {}

        async with aiohttp.ClientSession() as session:
            tasks = []
            for category in categories:
                task = self._download_single_category_async(session, category)
                tasks.append(task)

            category_results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, category in enumerate(categories):
                if isinstance(category_results[i], Exception):
                    results[str(category)] = {"error": str(category_results[i])}
                else:
                    results[str(category)] = category_results[i]

        end_time = time.time()
        return results, end_time - start_time

    async def _download_single_category_async(self, session: aiohttp.ClientSession, category: int) -> Any:
        """Асинхронная загрузка одной категории"""
        try:
            url = self._build_url(category)
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=self.batch_config.timeout)) as response:

                # Проверяем Content-Type
                content_type = response.headers.get('content-type', '')
                if 'application/json' in content_type:
                    data = await response.json()
                    logger.info(f"✅ Асинхронно загружена категория {category}")
                    return data
                else:
                    # Если не JSON, возвращаем информацию о ответе с обработкой кодировки
                    try:
                        text = await response.text()
                    except UnicodeDecodeError:
                        # Если ошибка кодировки, читаем как байты
                        bytes_data = await response.read()
                        text = bytes_data.decode('utf-8', errors='replace')

                    return {
                        "content_type": content_type,
                        "text_preview": text[:100] + "..." if len(text) > 100 else text,
                        "status_code": response.status,
                        "url": str(response.url)
                    }

        except Exception as e:
            logger.error(f"❌ Асинхронная ошибка категории {category}: {e}")
            return {"error": str(e)}

    def download_data_threaded(self, categories: List[int]) -> Dict[str, Any]:
        """Многопоточная загрузка данных"""
        logger.info(f"🎯 Многопоточная загрузка {len(categories)} категорий")
        results = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.batch_config.max_workers) as executor:
            future_to_category = {
                executor.submit(self._download_single_category_sync, category): category
                for category in categories
            }

            for future in concurrent.futures.as_completed(future_to_category):
                category = future_to_category[future]
                try:
                    results[str(category)] = future.result()
                    logger.info(f"✅ Потоковая загрузка категории {category}")
                except Exception as e:
                    logger.error(f"❌ Ошибка потока категории {category}: {e}")
                    results[str(category)] = {"error": str(e)}

        return results

    def _download_single_category_sync(self, category: int) -> Any:
        """Синхронная загрузка одной категории для многопоточности"""
        try:
            url = self._build_url(category)
            response = requests.get(url, timeout=self.batch_config.timeout)

            content_type = response.headers.get('content-type', '')
            if 'application/json' in content_type:
                return response.json()
            else:
                return {
                    "content_type": content_type,
                    "text_preview": response.text[:100] + "..." if len(response.text) > 100 else response.text,
                    "status_code": response.status_code
                }

        except Exception as e:
            raise e

    def download_data_batched(self, categories: List[int]) -> Dict[str, Any]:
        """Пакетная обработка данных с использованием numpy"""
        logger.info(f"📦 Пакетная обработка {len(categories)} категорий")

        if not categories:
            return {}

        # Разделяем категории на пакеты
        batches = np.array_split(categories, max(1, len(categories) // self.batch_config.batch_size))
        logger.info(f"📊 Создано {len(batches)} пакетов")

        all_results = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.batch_config.max_workers) as executor:
            future_to_batch = {
                executor.submit(self._process_batch, batch): i
                for i, batch in enumerate(batches)
            }

            for future in concurrent.futures.as_completed(future_to_batch):
                batch_num = future_to_batch[future]
                try:
                    batch_results = future.result()
                    all_results.update(batch_results)
                    logger.info(f"✅ Обработан пакет {batch_num + 1}/{len(batches)}")
                except Exception as e:
                    logger.error(f"❌ Ошибка пакета {batch_num}: {e}")

        return all_results

    def _process_batch(self, batch: np.ndarray) -> Dict[str, Any]:
        """Обработка одного пакета категорий"""
        batch_results = {}

        for category in batch:
            try:
                url = self._build_url(int(category))
                response = requests.get(url, timeout=self.batch_config.timeout)

                content_type = response.headers.get('content-type', '')
                if 'application/json' in content_type:
                    batch_results[str(category)] = response.json()
                else:
                    batch_results[str(category)] = {
                        "content_type": content_type,
                        "text_preview": response.text[:100] + "..." if len(response.text) > 100 else response.text,
                        "status_code": response.status_code
                    }

            except Exception as e:
                batch_results[str(category)] = {"error": str(e)}

        return batch_results

    def transform_to_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Преобразование данных в структурированный словарь"""
        logger.info("🔄 Преобразование данных в словарь")

        transformed = {
            "categories": {},
            "statistics": {
                "total": len(data),
                "successful": 0,
                "errors": 0,
                "non_json_responses": 0
            }
        }

        for category, category_data in data.items():
            if isinstance(category_data, dict) and "error" in category_data:
                transformed["categories"][category] = {
                    "status": "error",
                    "message": category_data["error"]
                }
                transformed["statistics"]["errors"] += 1
            elif isinstance(category_data, dict) and "content_type" in category_data:
                transformed["categories"][category] = {
                    "status": "non_json",
                    "content_type": category_data.get("content_type"),
                    "status_code": category_data.get("status_code"),
                    "preview": category_data.get("text_preview", "")
                }
                transformed["statistics"]["non_json_responses"] += 1
            else:
                transformed["categories"][category] = {
                    "status": "success",
                    "data": category_data,
                    "items_count": len(category_data) if isinstance(category_data, list) else 1
                }
                transformed["statistics"]["successful"] += 1

        return transformed

    def _build_url(self, category: int) -> str:
        """Построение URL для запроса"""
        params = {
            "id_cat": category,
            "skip": 0,
            "pricemin": 0,
            "price_max": 1060225
        }
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.base_url}?{query_string}"


# Бенчмарк для сравнения методов
class PerformanceBenchmark:
    @staticmethod
    def measure_time(func, *args, **kwargs) -> Tuple[Any, float]:
        """Измерение времени выполнения функции"""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return result, end_time - start_time


async def main():
    print("=" * 60)
    print("🚀 ПРОДВИНУТЫЙ PYTHON: Асинхронное программирование")
    print("=" * 60)

    loader = AdvancedWoysaLoader()
    benchmark = PerformanceBenchmark()

    # Тестовые категории (меньше для теста)
    test_categories = [100, 200, 300, 400, 500]

    print(f"📋 Тестовые категории: {test_categories}")
    print()

    # Синхронная загрузка
    print("1. 🔄 СИНХРОННАЯ ЗАГРУЗКА:")
    sync_data, sync_time = benchmark.measure_time(loader.download_data, test_categories)
    print(f"   ⏱️ Время: {sync_time:.2f} сек")
    print(f"   📊 Результаты: {len(sync_data)} категорий")

    # Многопоточная загрузка
    print("\n2. 🎯 МНОГОПОТОЧНАЯ ЗАГРУЗКА:")
    threaded_data, threaded_time = benchmark.measure_time(
        loader.download_data_threaded, test_categories
    )
    print(f"   ⏱️ Время: {threaded_time:.2f} сек")
    print(f"   📊 Результаты: {len(threaded_data)} категорий")

    # Пакетная обработка
    print("\n3. 📦 ПАКЕТНАЯ ОБРАБОТКА:")
    batched_data, batched_time = benchmark.measure_time(
        loader.download_data_batched, test_categories
    )
    print(f"   ⏱️ Время: {batched_time:.2f} сек")
    print(f"   📊 Результаты: {len(batched_data)} категорий")

    # Асинхронная загрузка
    print("\n4. ⚡ АСИНХРОННАЯ ЗАГРУЗКА:")
    async_data, async_time = await loader.download_data_async(test_categories)
    print(f"   ⏱️ Время: {async_time:.2f} сек")
    print(f"   📊 Результаты: {len(async_data)} категорий")

    # Преобразование данных
    print("\n5. 🔄 ПРЕОБРАЗОВАНИЕ ДАННЫХ:")
    transformed = loader.transform_to_dict(async_data)
    print(f"   📈 Статистика: {transformed['statistics']}")

    print("\n" + "=" * 60)
    print("🎯 СРАВНЕНИЕ ПРОИЗВОДИТЕЛЬНОСТИ:")
    print(f"   Синхронная:    {sync_time:.2f} сек")
    print(f"   Многопоточная: {threaded_time:.2f} сек")
    print(f"   Пакетная:      {batched_time:.2f} сек")
    print(f"   Асинхронная:   {async_time:.2f} сек")

    # Показываем примеры ответов
    print("\n📋 ПРИМЕРЫ ОТВЕТОВ:")
    for category in test_categories[:2]:  # Показываем первые 2 категории
        data = async_data.get(str(category), {})
        if isinstance(data, dict) and "error" in data:
            status = "❌ Ошибка"
        elif isinstance(data, dict) and "content_type" in data:
            status = "⚠️ HTML"
        else:
            status = "✅ JSON"
        print(f"   Категория {category}: {status}")
        if "content_type" in data:
            print(f"      Content-Type: {data.get('content_type')}")
            print(f"      Preview: {data.get('text_preview')}")
        if "error" in data:
            print(f"      Error: {data.get('error')}")


if __name__ == "__main__":
    asyncio.run(main())