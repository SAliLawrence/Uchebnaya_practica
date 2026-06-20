import argparse
import sys
from datetime import datetime, timedelta

from database import get_database
from data_export import DataExporter
from logger_config import logger
from models import Order, OrderItem


def parse_date_period(period: str) -> tuple:
    today = datetime.now().date()

    if period == 'day':
        start_date = today.strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
    elif period == 'week':
        start_date = (today - timedelta(days=7)).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
    elif period == 'month':
        start_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
    else:
        raise ValueError(f"Неизвестный период: {period}")

    return start_date, end_date


def cmd_report(args):
    db = get_database(args.db)

    if args.period:
        start_date, end_date = parse_date_period(args.period)
        revenue = db.get_revenue(start_date, end_date)
        print(f"\n=== Отчет за {args.period} ===")
        print(f"Период: {start_date} - {end_date}")
        print(f"Общая выручка: {revenue:.2f} руб.")

    print("\n=== Заказы по статусам ===")
    status_counts = db.get_orders_by_status_count()
    for status, count in status_counts.items():
        print(f"  {status}: {count}")

    print("\n=== Топ-3 клиента по сумме заказов ===")
    top_customers = db.get_top_customers(3)
    for i, customer in enumerate(top_customers, 1):
        print(f"  {i}. {customer['name']} - {customer['total_spent']:.2f} руб.")


def cmd_export(args):
    db = get_database(args.db)
    orders = db.get_all_orders()

    exporter = DataExporter()

    if args.file.endswith('.json'):
        success = exporter.export_to_json(orders, args.file)
    elif args.file.endswith('.xml'):
        success = exporter.export_to_xml(orders, args.file)
    else:
        print("Ошибка: файл должен иметь расширение .json или .xml")
        sys.exit(1)

    if success:
        print(f"Успешно экспортировано {len(orders)} заказов в {args.file}")
    else:
        print("Ошибка при экспорте")
        sys.exit(1)


def cmd_import(args):
    db = get_database(args.db)
    exporter = DataExporter()

    if args.file.endswith('.json'):
        orders_data = exporter.import_from_json(args.file)
    elif args.file.endswith('.xml'):
        orders_data = exporter.import_from_xml(args.file)
    else:
        print("Ошибка: файл должен иметь расширение .json или .xml")
        sys.exit(1)

    if not orders_data:
        print("Нет данных для импорта")
        sys.exit(1)

    imported_count = 0
    for order_data in orders_data:
        if not exporter.validate_order_data(order_data):
            print(f"Пропущен некорректный заказ: {order_data}")
            continue

        customer = db.get_customer(order_data['customer_id'])
        if not customer:
            print(f"Клиент с ID {order_data['customer_id']} не найден, пропускаем заказ")
            continue

        items = [OrderItem.from_dict(item) for item in order_data.get('items', [])]

        try:
            db.add_order(
                customer_id=order_data['customer_id'],
                order_date=order_data['order_date'],
                status=order_data['status'],
                total=order_data['total'],
                items=[item.to_dict() for item in items]
            )
            imported_count += 1
        except Exception as e:
            logger.error(f"Ошибка при импорте заказа: {e}")

    print(f"Импортировано {imported_count} заказов из {args.file}")


def cmd_list_customers(args):
    db = get_database(args.db)
    customers = db.get_all_customers()

    print("\n=== Список клиентов ===")
    for customer in customers:
        print(
            f"ID: {customer['id']}, Имя: {customer['name']}, Телефон: {customer.get('phone', '')}, Адрес: {customer.get('address', '')}")


def cmd_add_customer(args):
    db = get_database(args.db)
    customer_id = db.add_customer(args.name, args.phone, args.address)
    print(f"Клиент добавлен с ID: {customer_id}")


def cmd_list_orders(args):
    db = get_database(args.db)
    orders = db.get_all_orders(status=args.status)

    print("\n=== Список заказов ===")
    for order in orders:
        print(
            f"ID: {order['id']}, Клиент: {order.get('customer_name', '')}, Дата: {order['order_date']}, Статус: {order['status']}, Сумма: {order['total']:.2f}")


def main():
    parser = argparse.ArgumentParser(description='Система учета заказов "Быстрая доставка"')
    parser.add_argument('--db', choices=['sqlite', 'tinydb'], default='sqlite',
                        help='Тип базы данных (по умолчанию: sqlite)')

    subparsers = parser.add_subparsers(dest='command', help='Доступные команды')

    report_parser = subparsers.add_parser('report', help='Показать отчет')
    report_parser.add_argument('--period', choices=['day', 'week', 'month'], required=True,
                               help='Период для отчета')

    export_parser = subparsers.add_parser('export', help='Экспорт заказов')
    export_parser.add_argument('--file', required=True, help='Путь к файлу для экспорта')

    import_parser = subpar
