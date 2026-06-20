from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
from logger_config import logger


@dataclass
class OrderItem:
    product_name: str
    quantity: int
    price: float

    @property
    def total(self) -> float:
        return self.quantity * self.price

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'OrderItem':
        return cls(
            product_name=data['product_name'],
            quantity=data['quantity'],
            price=data['price']
        )


@dataclass
class Customer:
    name: str
    phone: str
    address: str
    id: Optional[int] = None

    def to_dict(self) -> Dict:
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict) -> 'Customer':
        return cls(
            id=data.get('id'),
            name=data['name'],
            phone=data.get('phone', ''),
            address=data.get('address', '')
        )


@dataclass
class Order:
    customer_id: int
    order_date: str
    status: str
    total: float
    items: List[OrderItem] = field(default_factory=list)
    id: Optional[int] = None
    customer_name: Optional[str] = None

    VALID_STATUSES = ['новый', 'в доставке', 'выполнен', 'отменён']

    def __post_init__(self):
        if self.status not in self.VALID_STATUSES:
            raise ValueError(f"Неверный статус. Допустимые: {self.VALID_STATUSES}")

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'order_date': self.order_date,
            'status': self.status,
            'total': self.total,
            'items': [item.to_dict() for item in self.items],
            'customer_name': self.customer_name
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Order':
        items = [OrderItem.from_dict(item) for item in data.get('items', [])]
        return cls(
            id=data.get('id'),
            customer_id=data['customer_id'],
            order_date=data['order_date'],
            status=data['status'],
            total=data['total'],
            items=items,
            customer_name=data.get('customer_name')
        )

    @staticmethod
    def calculate_total(items: List[OrderItem]) -> float:
        return sum(item.total for item in items)
