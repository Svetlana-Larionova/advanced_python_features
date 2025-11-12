"""
Кэширование с использованием Redis
"""
import redis
import json
import pickle
from typing import Any, Optional
import logging
from functools import wraps
import hashlib

logger = logging.getLogger(__name__)


class RedisCache:
    """
    Класс для работы с Redis кэшем
    Соответствует требованию 01
    """

    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0, password: Optional[str] = None):
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True
        )
        self.default_ttl = 300  # 5 минут по умолчанию

    def is_connected(self) -> bool:
        """Проверка подключения к Redis"""
        try:
            self.redis_client.ping()
            return True
        except redis.ConnectionError:
            logger.error("❌ Не удалось подключиться к Redis")
            return False

    def get(self, key: str) -> Optional[Any]:
        """Получение данных из кэша"""
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                return pickle.loads(cached_data.encode('latin1'))
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка получения из кэша: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Сохранение данных в кэш"""
        try:
            ttl = ttl or self.default_ttl
            serialized_value = pickle.dumps(value).decode('latin1')
            self.redis_client.setex(key, ttl, serialized_value)
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения в кэш: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Удаление данных из кэша"""
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка удаления из кэша: {e}")
            return False

    def clear_pattern(self, pattern: str) -> bool:
        """Удаление данных по шаблону"""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка очистки кэша по шаблону: {e}")
            return False

    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Генерация ключа для кэша"""
        key_data = f"{prefix}:{str(args)}:{str(kwargs)}"
        return f"cache:{hashlib.md5(key_data.encode()).hexdigest()}"


# Глобальный экземпляр кэша
cache = RedisCache()


def cached(ttl: int = 300):
    """
    Декоратор для кэширования результатов функций
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Генерируем ключ на основе функции и аргументов
            key = cache.generate_key(func.__name__, *args, **kwargs)

            # Пробуем получить из кэша
            cached_result = cache.get(key)
            if cached_result is not None:
                logger.info(f"✅ Данные получены из кэша: {key}")
                return cached_result

            # Выполняем функцию если нет в кэше
            result = func(*args, **kwargs)

            # Сохраняем в кэш
            cache.set(key, result, ttl)
            logger.info(f"💾 Данные сохранены в кэш: {key}")

            return result

        return wrapper

    return decorator


def invalidate_cache(pattern: str):
    """
    Декоратор для инвалидации кэша
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            cache.clear_pattern(pattern)
            logger.info(f"🗑️  Кэш очищен по шаблону: {pattern}")
            return result

        return wrapper

    return decorator