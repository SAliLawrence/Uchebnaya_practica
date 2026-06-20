import pytest
import os
import tempfile
from database import SQLiteDatabase, TinyDBDatabase


# Тесты для SQLiteDatabase
@pytest.fixture
def sqlite_db():
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db = SQLiteDatabase(f.name)
        yield db
        os.unlink(f.name)


def test_update_customer(sqlite_db):
    customer_id = sqlite_db.add_customer("Тест", "123", "Адрес")
    assert sqlite_db.update_customer(customer_id, "Новое имя", "456", "Новый адрес")
    updated = sqlite_db.get_customer(customer_id)
    assert updated['name'] == "Новое имя"


def test_delete_customer(sqlite_db):
    customer_id = sqlite_db.add_customer("Тест", "123", "Адрес")
    assert sqlite_db.delete_customer(customer_id)
    assert sqlite_db.get_customer(customer_id) is None


def test_cannot_delete_customer_with_orders(sqlite_db):
    customer_id = sqlite_db.add_customer("Тест", "123", "Адрес")
    sqlite_db.add_order(customer_id, "2025-01-01", "новый", 100, [])
    assert not sqlite_db.delete_customer(customer_id)


def test_add_order(sqlite_db):
    customer_id = sqlite_db.add_customer("Тест", "123", "Адрес")
    order_id = sqlite_db.add_order(customer_id, "2025-01-01", "новый", 100,
                                   [{"product_name": "Товар", "quantity": 1, "price": 100}])
    assert order_id is not None
    order = sqlite_db.get_order(order_id)
    assert order['status'] == "новый"


def test_update_order(sqlite_db):
    customer_id = sqlite_db.add_customer("Тест", "123", "Адрес")
    order_id = sqlite_db.add_order(customer_id, "2025-01-01", "новый", 100, [])
    assert sqlite_db.update_order(order_id, customer_id, "2025-01-02", "выполнен", 150, [])
    updated = sqlite_db.get_order(order_id)
    assert updated['status'] == "выполнен"


def test_delete_order(sqlite_db):
    customer_id = sqlite_db.add_customer("Тест", "123", "Адрес")
    order_id = sqlite_db.add_order(customer_id, "2025-01-01", "новый", 100, [])
    assert sqlite_db.delete_order(order_id)
    assert sqlite_db.get_order(order_id) is None


def test_get_orders_by_status_count(sqlite_db):
    customer_id = sqlite_db.add_customer("Тест", "123", "Адрес")
    sqlite_db.add_order(customer_id, "2025-01-01", "новый", 100, [])
    sqlite_db.add_order(customer_id, "2025-01-02", "новый", 100, [])
    sqlite_db.add_order(customer_id, "2025-01-03", "выполнен", 100, [])

    counts = sqlite_db.get_orders_by_status_count()
    assert counts['новый'] == 2
    assert counts['выполнен'] == 1


def test_get_revenue(sqlite_db):
    customer_id = sqlite_db.add_customer("Тест", "123", "Адрес")
    sqlite_db.add_order(customer_id, "2025-01-01", "выполнен", 100, [])
    sqlite_db.add_order(customer_id, "2025-01-02", "выполнен", 200, [])
    sqlite_db.add_order(customer_id, "2025-01-03", "новый", 300, [])

    revenue = sqlite_db.get_revenue("2025-01-01", "2025-01-31")
    assert revenue == 300  # Только выполненные


def test_get_all_orders_with_filter(sqlite_db):
    customer_id = sqlite_db.add_customer("Тест", "123", "Адрес")
    sqlite_db.add_order(customer_id, "2025-01-01", "новый", 100, [])
    sqlite_db.add_order(customer_id, "2025-01-02", "выполнен", 100, [])

    new_orders = sqlite_db.get_all_orders(status="новый")
    assert len(new_orders) == 1


# Тесты для TinyDBDatabase
@pytest.fixture
def tinydb_db():
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        db = TinyDBDatabase(f.name)
        yield db
        os.unlink(f.name)


def test_tinydb_add_customer(tinydb_db):
    customer_id = tinydb_db.add_customer("Тест", "123", "Адрес")
    assert customer_id is not None


def test_tinydb_get_all_customers(tinydb_db):
    tinydb_db.add_customer("Тест1", "123", "Адрес1")
    tinydb_db.add_customer("Тест2", "456", "Адрес2")
    customers = tinydb_db.get_all_customers()
    assert len(customers) == 2


def test_tinydb_add_order(tinydb_db):
    customer_id = tinydb_db.add_customer("Тест", "123", "Адрес")
    order_id = tinydb_db.add_order(customer_id, "2025-01-01", "новый", 100, [])
    assert order_id is not None
