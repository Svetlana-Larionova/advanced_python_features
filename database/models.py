"""
Модели таблиц базы данных
"""
from sqlalchemy import Column, String, Text, Numeric, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .base import BaseTable, Base
import logging

logger = logging.getLogger(__name__)


class Supplier(BaseTable):
    """
    Модель таблицы поставщиков
    Соответствует требованию 03.B
    """
    __tablename__ = "suppliers"

    name = Column(String(255), nullable=False, index=True)
    contact_person = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    address = Column(Text)
    is_active = Column(Boolean, default=True)

    # Связь с товарами
    products = relationship("Product", back_populates="supplier")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logger.info(f"Создан новый поставщик: {self.name}")


class Product(BaseTable):
    """
    Модель таблицы товаров
    Соответствует требованию 03.C
    """
    __tablename__ = "products"

    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    price = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Integer, default=0)
    category = Column(String(100))
    sku = Column(String(100), unique=True, index=True)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=False)
    is_available = Column(Boolean, default=True)

    # Связи
    supplier = relationship("Supplier", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logger.info(f"Создан новый товар: {self.name}")


class Order(BaseTable):
    """
    Модель таблицы заказов
    Соответствует требованию 03.A
    """
    __tablename__ = "orders"

    customer_name = Column(String(255), nullable=False)
    customer_email = Column(String(255))
    customer_phone = Column(String(50))
    total_amount = Column(Numeric(10, 2), default=0)
    status = Column(String(50), default="pending")  # pending, completed, cancelled
    shipping_address = Column(Text)

    # Связь с элементами заказа
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logger.info(f"Создан новый заказ для: {self.customer_name}")


class OrderItem(BaseTable):
    """
    Модель таблицы элементов заказа (связь многие-ко-многим)
    """
    __tablename__ = "order_items"

    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(10, 2), nullable=False)

    # Связи
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logger.info(f"Создан элемент заказа: {self.product_id} x {self.quantity}")