import pytest
import os
import tempfile
from database import SQLiteDatabase, TinyDBDatabase


@pytest.fixture
def sqlite_db():
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db = SQLiteDatabase(f.name)
        yield db
        os.unlink(f.name)


def test_add_customer(sqlite_db):
    customer_id = sqlite_db.add_customer("Тест", "123", "Адрес")
    assert customer_id is not None


def test_get_customer(sqlite_db):
    customer_id = sqlite_db.add_customer("Тест", "123", "Адрес")
    customer = sqlite_db.get_customer(customer_id)
    assert customer['name'] == "Тест"
