import os
import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

import sqlite3

try:
    from tinydb import TinyDB, Query

    TINYDB_AVAILABLE = True
except ImportError:
    TINYDB_AVAILABLE = False

from logger_config import logger

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)


class DatabaseInterface(ABC):

    @abstractmethod
    def init_db(self):
        pass

    @abstractmethod
    def get_all_customers(self) -> List[Dict]:
        pass

    @abstractmethod
    def get_customer(self, customer_id: int) -> Optional[Dict]:
        pass

    @abstractmethod
    def add_customer(self, name: str, phone: str, address: str) -> int:
        pass

    @abstractmethod
    def update_customer(self, customer_id: int, name: str, phone: str, address: str) -> bool:
        pass

    @abstractmethod
    def delete_customer(self, customer_id: int) -> bool:
        pass

    @abstractmethod
    def customer_has_orders(self, customer_id: int) -> bool:
        pass

    @abstractmethod
    def get_all_orders(self, status: Optional[str] = None, start_date: Optional[str] = None,
                       end_date: Optional[str] = None) -> List[Dict]:
        pass

    @abstractmethod
    def get_order(self, order_id: int) -> Optional[Dict]:
        pass

    @abstractmethod
    def add_order(self, customer_id: int, order_date: str, status: str,
                  total: float, items: List[Dict]) -> int:
        pass

    @abstractmethod
    def update_order(self, order_id: int, customer_id: int, order_date: str,
                     status: str, total: float, items: List[Dict]) -> bool:
        pass

    @abstractmethod
    def delete_order(self, order_id: int) -> bool:
        pass

    @abstractmethod
    def get_orders_by_status_count(self) -> Dict[str, int]:
        pass

    @abstractmethod
    def get_top_customers(self, limit: int = 3) -> List[Dict]:
        pass

    @abstractmethod
    def get_revenue(self, start_date: str, end_date: str) -> float:
        pass

    @abstractmethod
    def get_order_items(self, order_id: int) -> List[Dict]:
        pass


class SQLiteDatabase(DatabaseInterface):

    def __init__(self, db_path: str = os.path.join(DATA_DIR, "delivery.db")):
        self.db_path = db_path
        self.init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT,
                    address TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL,
                    order_date TEXT NOT NULL,
                    status TEXT CHECK(status IN ('новый', 'в доставке', 'выполнен', 'отменён')),
                    total REAL NOT NULL,
                    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE RESTRICT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    product_name TEXT,
                    quantity INTEGER,
                    price REAL,
                    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
                )
            """)
            conn.commit()
            logger.info("SQLite база данных инициализирована")

    def get_all_customers(self) -> List[Dict]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM customers ORDER BY id")
            return [dict(row) for row in cursor.fetchall()]

    def get_customer(self, customer_id: int) -> Optional[Dict]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def add_customer(self, name: str, phone: str, address: str) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO customers (name, phone, address) VALUES (?, ?, ?)",
                (name, phone, address)
            )
            conn.commit()
            logger.info(f"Добавлен клиент: {name}")
            return cursor.lastrowid

    def update_customer(self, customer_id: int, name: str, phone: str, address: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE customers SET name = ?, phone = ?, address = ? WHERE id = ?",
                (name, phone, address, customer_id)
            )
            conn.commit()
            updated = cursor.rowcount > 0
            if updated:
                logger.info(f"Обновлен клиент ID: {customer_id}")
            return updated

    def delete_customer(self, customer_id: int) -> bool:
        if self.customer_has_orders(customer_id):
            logger.warning(f"Нельзя удалить клиента {customer_id} - есть заказы")
            return False
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
            conn.commit()
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Удален клиент ID: {customer_id}")
            return deleted

    def customer_has_orders(self, customer_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM orders WHERE customer_id = ?", (customer_id,))
            count = cursor.fetchone()[0]
            return count > 0

    def get_all_orders(self, status: Optional[str] = None, start_date: Optional[str] = None,
                       end_date: Optional[str] = None) -> List[Dict]:
        query = "SELECT o.*, c.name as customer_name FROM orders o JOIN customers c ON o.customer_id = c.id WHERE 1=1"
        params = []

        if status:
            query += " AND o.status = ?"
            params.append(status)
        if start_date:
            query += " AND o.order_date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND o.order_date <= ?"
            params.append(end_date)

        query += " ORDER BY o.order_date DESC"

        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            orders = [dict(row) for row in cursor.fetchall()]

            for order in orders:
                order['items'] = self.get_order_items(order['id'])

            return orders

    def get_order(self, order_id: int) -> Optional[Dict]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT o.*, c.name as customer_name 
                FROM orders o 
                JOIN customers c ON o.customer_id = c.id 
                WHERE o.id = ?
            """, (order_id,))
            row = cursor.fetchone()
            if row:
                order = dict(row)
                order['items'] = self.get_order_items(order_id)
                return order
            return None

    def add_order(self, customer_id: int, order_date: str, status: str,
                  total: float, items: List[Dict]) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO orders (customer_id, order_date, status, total) VALUES (?, ?, ?, ?)",
                (customer_id, order_date, status, total)
            )
            order_id = cursor.lastrowid

            for item in items:
                cursor.execute(
                    "INSERT INTO order_items (order_id, product_name, quantity, price) VALUES (?, ?, ?, ?)",
                    (order_id, item['product_name'], item['quantity'], item['price'])
                )

            conn.commit()
            logger.info(f"Добавлен заказ ID: {order_id}")
            return order_id

    def update_order(self, order_id: int, customer_id: int, order_date: str,
                     status: str, total: float, items: List[Dict]) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE orders SET customer_id = ?, order_date = ?, status = ?, total = ? WHERE id = ?",
                (customer_id, order_date, status, total, order_id)
            )

            cursor.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))

            for item in items:
                cursor.execute(
                    "INSERT INTO order_items (order_id, product_name, quantity, price) VALUES (?, ?, ?, ?)",
                    (order_id, item['product_name'], item['quantity'], item['price'])
                )

            conn.commit()
            updated = cursor.rowcount > 0
            if updated:
                logger.info(f"Обновлен заказ ID: {order_id}")
            return updated

    def delete_order(self, order_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
            conn.commit()
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Удален заказ ID: {order_id}")
            return deleted

    def get_order_items(self, order_id: int) -> List[Dict]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT id, product_name, quantity, price FROM order_items WHERE order_id = ?", (order_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_orders_by_status_count(self) -> Dict[str, int]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM orders 
                GROUP BY status
            """)
            result = {row[0]: row[1] for row in cursor.fetchall()}
            for status in ['новый', 'в доставке', 'выполнен', 'отменён']:
                result.setdefault(status, 0)
            return result

    def get_top_customers(self, limit: int = 3) -> List[Dict]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.id, c.name, c.phone, c.address, SUM(o.total) as total_spent
                FROM customers c
                JOIN orders o ON c.id = o.customer_id
                WHERE o.status = 'выполнен'
                GROUP BY c.id
                ORDER BY total_spent DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_revenue(self, start_date: str, end_date: str) -> float:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COALESCE(SUM(total), 0) as revenue
                FROM orders
                WHERE status = 'выполнен' AND order_date BETWEEN ? AND ?
            """, (start_date, end_date))
            return cursor.fetchone()[0]


class TinyDBDatabase(DatabaseInterface):

    def __init__(self, db_path: str = os.path.join(DATA_DIR, "tinydb.json")):
        if not TINYDB_AVAILABLE:
            raise ImportError("TinyDB не установлен. Установите: pip install tinydb")
        self.db_path = db_path
        self.db = TinyDB(db_path)
        self.customers_table = self.db.table('customers')
        self.orders_table = self.db.table('orders')
        self._next_ids = {}
        self.init_db()

    def _get_next_id(self, table_name: str) -> int:
        if table_name not in self._next_ids:
            table = self.db.table(table_name)
            records = table.all()
            self._next_ids[table_name] = max([r.get('id', 0) for r in records], default=0) + 1
        result = self._next_ids[table_name]
        self._next_ids[table_name] += 1
        return result

    def init_db(self):
        logger.info("TinyDB инициализирована")

    def get_all_customers(self) -> List[Dict]:
        return self.customers_table.all()

    def get_customer(self, customer_id: int) -> Optional[Dict]:
        Customer = Query()
        result = self.customers_table.search(Customer.id == customer_id)
        return result[0] if result else None

    def add_customer(self, name: str, phone: str, address: str) -> int:
        customer_id = self._get_next_id('customers')
        customer = {'id': customer_id, 'name': name, 'phone': phone, 'address': address}
        self.customers_table.insert(customer)
        logger.info(f"Добавлен клиент: {name}")
        return customer_id

    def update_customer(self, customer_id: int, name: str, phone: str, address: str) -> bool:
        Customer = Query()
        updated = self.customers_table.update(
            {'name': name, 'phone': phone, 'address': address},
            Customer.id == customer_id
        )
        if updated:
            logger.info(f"Обновлен клиент ID: {customer_id}")
        return len(updated) > 0

    def delete_customer(self, customer_id: int) -> bool:
        if self.customer_has_orders(customer_id):
            logger.warning(f"Нельзя удалить клиента {customer_id} - есть заказы")
            return False
        Customer = Query()
        deleted = self.customers_table.remove(Customer.id == customer_id)
        if deleted:
            logger.info(f"Удален клиент ID: {customer_id}")
        return len(deleted) > 0

    def customer_has_orders(self, customer_id: int) -> bool:
        Order = Query()
        orders = self.orders_table.search(Order.customer_id == customer_id)
        return len(orders) > 0

    def get_all_orders(self, status: Optional[str] = None, start_date: Optional[str] = None,
                       end_date: Optional[str] = None) -> List[Dict]:
        orders = self.orders_table.all()

        if status:
            orders = [o for o in orders if o['status'] == status]
        if start_date:
            orders = [o for o in orders if o['order_date'] >= start_date]
        if end_date:
            orders = [o for o in orders if o['order_date'] <= end_date]

        for order in orders:
            customer = self.get_customer(order['customer_id'])
            order['customer_name'] = customer['name'] if customer else 'Неизвестно'

        orders.sort(key=lambda x: x['order_date'], reverse=True)
        return orders

    def get_order(self, order_id: int) -> Optional[Dict]:
        Order = Query()
        result = self.orders_table.search(Order.id == order_id)
        if result:
            order = result[0]
            customer = self.get_customer(order['customer_id'])
            order['customer_name'] = customer['name'] if customer else 'Неизвестно'
            return order
        return None

    def add_order(self, customer_id: int, order_date: str, status: str,
                  total: float, items: List[Dict]) -> int:
        order_id = self._get_next_id('orders')
        order = {
            'id': order_id,
            'customer_id': customer_id,
            'order_date': order_date,
            'status': status,
            'total': total,
            'items': items
        }
        self.orders_table.insert(order)
        logger.info(f"Добавлен заказ ID: {order_id}")
        return order_id

    def update_order(self, order_id: int, customer_id: int, order_date: str,
                     status: str, total: float, items: List[Dict]) -> bool:
        Order = Query()
        updated = self.orders_table.update(
            {'customer_id': customer_id, 'order_date': order_date, 'status': status, 'total': total, 'items': items},
            Order.id == order_id
        )
        if updated:
            logger.info(f"Обновлен заказ ID: {order_id}")
        return len(updated) > 0

    def delete_order(self, order_id: int) -> bool:
        Order = Query()
        deleted = self.orders_table.remove(Order.id == order_id)
        if deleted:
            logger.info(f"Удален заказ ID: {order_id}")
        return len(deleted) > 0

    def get_order_items(self, order_id: int) -> List[Dict]:
        order = self.get_order(order_id)
        return order.get('items', []) if order else []

    def get_orders_by_status_count(self) -> Dict[str, int]:
        orders = self.orders_table.all()
        result = {'новый': 0, 'в доставке': 0, 'выполнен': 0, 'отменён': 0}
        for order in orders:
            result[order['status']] = result.get(order['status'], 0) + 1
        return result

    def get_top_customers(self, limit: int = 3) -> List[Dict]:
        orders = self.orders_table.all()
        customer_totals = {}

        for order in orders:
            if order['status'] == 'выполнен':
                customer_totals[order['customer_id']] = customer_totals.get(order['customer_id'], 0) + order['total']

        sorted_customers = sorted(customer_totals.items(), key=lambda x: x[1], reverse=True)[:limit]

        result = []
        for cust_id, total in sorted_customers:
            customer = self.get_customer(cust_id)
            if customer:
                result.append({
                    'id': cust_id,
                    'name': customer['name'],
                    'phone': customer['phone'],
                    'address': customer['address'],
                    'total_spent': total
                })
        return result

    def get_revenue(self, start_date: str, end_date: str) -> float:
        orders = self.orders_table.all()
        revenue = 0
        for order in orders:
            if order['status'] == 'выполнен' and start_date <= order['order_date'] <= end_date:
                revenue += order['total']
        return revenue


def get_database(db_type: str = "sqlite") -> DatabaseInterface:
    if db_type == "sqlite":
        return SQLiteDatabase()
    elif db_type == "tinydb":
        return TinyDBDatabase()
    else:
        raise ValueError(f"Неподдерживаемый тип БД: {db_type}")
