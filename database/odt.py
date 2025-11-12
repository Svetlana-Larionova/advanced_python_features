"""
ODT (Object Data Transfer) классы для преобразования данных
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class SupplierODT:
    """
    ODT класс для поставщика
    Соответствует требованию K4
    """
    id: Optional[int] = None
    name: str = ""
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь"""
        return asdict(self)

    def __str__(self) -> str:
        return f"SupplierODT(id={self.id}, name='{self.name}', email='{self.email}')"


@dataclass
class ProductODT:
    """
    ODT класс для товара
    """
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    price: float = 0.0
    quantity: int = 0
    category: Optional[str] = None
    sku: Optional[str] = None
    supplier_id: Optional[int] = None
    is_available: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    supplier_name: Optional[str] = None  # Дополнительное поле для удобства

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь"""
        return asdict(self)

    def __str__(self) -> str:
        return f"ProductODT(id={self.id}, name='{self.name}', price={self.price}, category='{self.category}')"


@dataclass
class OrderItemODT:
    """
    ODT класс для элемента заказа
    """
    id: Optional[int] = None
    order_id: Optional[int] = None
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    quantity: int = 1
    unit_price: float = 0.0
    total_price: float = 0.0
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Автоматический расчет общей цены"""
        self.total_price = self.quantity * self.unit_price

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь"""
        return asdict(self)


@dataclass
class OrderODT:
    """
    ODT класс для заказа
    """
    id: Optional[int] = None
    customer_name: str = ""
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    total_amount: float = 0.0
    status: str = "pending"
    shipping_address: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    items: List[OrderItemODT] = None

    def __post_init__(self):
        """Инициализация списка элементов"""
        if self.items is None:
            self.items = []

    def add_item(self, item: OrderItemODT):
        """Добавление элемента заказа"""
        self.items.append(item)
        self.total_amount += item.total_price

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь"""
        result = asdict(self)
        result['items'] = [item.to_dict() for item in self.items]
        return result

    def __str__(self) -> str:
        return f"OrderODT(id={self.id}, customer='{self.customer_name}', total={self.total_amount}, items={len(self.items)})"


class ODTConverter:
    """
    Класс для преобразования моделей SQLAlchemy в ODT
    Соответствует требованию K5
    """

    @staticmethod
    def supplier_to_odt(supplier) -> SupplierODT:
        """Преобразование Supplier в SupplierODT"""
        return SupplierODT(
            id=supplier.id,
            name=supplier.name,
            contact_person=supplier.contact_person,
            email=supplier.email,
            phone=supplier.phone,
            address=supplier.address,
            is_active=supplier.is_active,
            created_at=supplier.created_at,
            updated_at=supplier.updated_at
        )

    @staticmethod
    def product_to_odt(product, include_supplier_name: bool = False) -> ProductODT:
        """Преобразование Product в ProductODT"""
        supplier_name = product.supplier.name if include_supplier_name and product.supplier else None

        return ProductODT(
            id=product.id,
            name=product.name,
            description=product.description,
            price=float(product.price),
            quantity=product.quantity,
            category=product.category,
            sku=product.sku,
            supplier_id=product.supplier_id,
            is_available=product.is_available,
            created_at=product.created_at,
            updated_at=product.updated_at,
            supplier_name=supplier_name
        )

    @staticmethod
    def order_to_odt(order) -> OrderODT:
        """Преобразование Order в OrderODT"""
        order_odt = OrderODT(
            id=order.id,
            customer_name=order.customer_name,
            customer_email=order.customer_email,
            customer_phone=order.customer_phone,
            total_amount=float(order.total_amount),
            status=order.status,
            shipping_address=order.shipping_address,
            created_at=order.created_at,
            updated_at=order.updated_at
        )

        # Добавляем элементы заказа
        for item in order.order_items:
            item_odt = OrderItemODT(
                id=item.id,
                order_id=item.order_id,
                product_id=item.product_id,
                product_name=item.product.name if item.product else None,
                quantity=item.quantity,
                unit_price=float(item.unit_price),
                created_at=item.created_at
            )
            order_odt.add_item(item_odt)

        return order_odt