"""
Абстрактный базовый класс для таблиц
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import func
from datetime import datetime
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# Базовый класс для всех моделей
Base = declarative_base()


class BaseTable(Base):
    """
    Абстрактный базовый класс для всех таблиц
    Соответствует требованию K2
    """
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def __init__(self, **kwargs):
        """
        Конструктор, который заполняет все поля класса
        Соответствует требованию 02.A
        """
        super().__init__()
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                logger.debug(f"Установлено поле {key} = {value}")
            else:
                logger.warning(f"Поле {key} не существует в классе {self.__class__.__name__}")

    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразование объекта в словарь

        Returns:
            Dict[str, Any]: Словарь с данными объекта
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            # Преобразуем datetime в строку для JSON-сериализации
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result

    def update(self, **kwargs) -> None:
        """
        Обновление полей объекта

        Args:
            **kwargs: Поля для обновления
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                logger.warning(f"Поле {key} не существует в классе {self.__class__.__name__}")

    def __repr__(self) -> str:
        """Строковое представление объекта"""
        return f"<{self.__class__.__name__}(id={self.id})>"