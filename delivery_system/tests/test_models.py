import pytest
from models import Customer, Order, OrderItem

def test_customer_creation():
    customer = Customer(name="Иван", phone="123", address="Москва")
    assert customer.name == "Иван"

def test_order_item_total():
    item = OrderItem(product_name="Товар", quantity=2, price=100)
    assert item.total == 200

def test_order_calculate_total():
    items = [OrderItem("A", 2, 100), OrderItem("B", 1, 50)]
    total = Order.calculate_total(items)
    assert total == 250
