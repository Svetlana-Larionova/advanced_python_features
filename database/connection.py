"""
Класс подключения к базе данных
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """
    Класс для управления подключением к базе данных
    Соответствует требованию K1
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._is_connected = False

    def connect(self, connection_string: str, **kwargs) -> bool:
        """
        Подключение к базе данных

        Args:
            connection_string: Строка подключения к БД
            **kwargs: Дополнительные параметры для create_engine

        Returns:
            bool: True если подключение успешно, False в противном случае
        """
        try:
            # Создаем движок SQLAlchemy
            self.engine = create_engine(connection_string, **kwargs)

            # Создаем фабрику сессий
            self.SessionLocal = scoped_session(
                sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            )

            # Проверяем подключение
            with self.engine.connect() as conn:
                logger.info("✅ Успешное подключение к базе данных")

            self._is_connected = True
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка подключения к базе данных: {e}")
            self._is_connected = False
            return False

    def get_session(self):
        """
        Получение сессии базы данных

        Returns:
            Session: Сессия SQLAlchemy
        """
        if not self._is_connected or self.SessionLocal is None:
            raise RuntimeError("База данных не подключена. Вызовите connect() сначала.")

        return self.SessionLocal()

    def close_connection(self):
        """Закрытие подключения к базе данных"""
        if self.SessionLocal:
            self.SessionLocal.remove()
        if self.engine:
            self.engine.dispose()
        self._is_connected = False
        logger.info("🔌 Подключение к базе данных закрыто")

    @property
    def is_connected(self) -> bool:
        """Статус подключения"""
        return self._is_connected

    def create_tables(self, base):
        """
        Создание всех таблиц в базе данных

        Args:
            base: Базовый класс декларативной базы
        """
        if not self._is_connected:
            raise RuntimeError("База данных не подключена")

        try:
            base.metadata.create_all(bind=self.engine)
            logger.info("✅ Таблицы успешно созданы в базе данных")
        except Exception as e:
            logger.error(f"❌ Ошибка создания таблиц: {e}")
            raise