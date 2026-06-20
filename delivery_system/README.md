# Система учета заказов "Быстрая доставка"

Внутреннее приложение для учёта заказов компании «Быстрая доставка».

## Требования

- Python 3.8+
- pytest (для тестирования)
- tinydb (опционально, если нужна TinyDB)

## Установка

```bash
pip install -r requirements.txt
```

Если планируете использовать TinyDB:
```bash
pip install tinydb
```

## Запуск

### GUI режим (Tkinter)
```bash
python main_gui.py
```

### CLI режим (argparse)

```bash
# Отчет за период (день/неделя/месяц)
python main_cli.py report --period month

# Экспорт заказов в JSON
python main_cli.py export --file orders_backup.json

# Экспорт заказов в XML
python main_cli.py export --file orders_backup.xml

# Импорт заказов из JSON
python main_cli.py import --file orders_new.json

# Импорт заказов из XML
python main_cli.py import --file new_orders.xml

# Список всех клиентов
python main_cli.py list-customers

# Добавление нового клиента
python main_cli.py add-customer --name "Иван Петров" --phone "+7 (912) 345-67-89" --address "г. Москва, ул. Ленина, д.1"

# Список заказов с фильтрацией по статусу
python main_cli.py list-orders --status "новый"
```

Выбор базы данных:
```bash
# По умолчанию используется SQLite
python main_cli.py report --period month

# Использование TinyDB
python main_cli.py --db tinydb report --period month
```

## Структура проекта

├── main_cli.py            # CLI-точка входа (argparse)
├── main_gui.py            # GUI-точка входа (Tkinter)
├── database.py            # Работа с БД (SQLite и TinyDB)
├── models.py              # Классы Customer, Order, OrderItem
├── data_export.py         # Экспорт/импорт XML/JSON
├── logger_config.py       # Настройка логирования
├── requirements.txt       # Список зависимостей
├── README.md              # Инструкция по установке и запуску
├── tests/
│   ├── __init__.py
│   ├── test_database.py
│   ├── test_models.py
│   └── test_export.py
├── logs/                  # Папка для логов
└── data/

## Тестирование

```bash
# Запуск всех тестов
pytest tests/ -v

# Запуск с покрытием кода
pytest tests/ --cov=database --cov=models --cov=data_export -v
```

## Функционал

### GUI
- Список заказов с фильтрами по статусу и дате
- Добавление/редактирование/удаление заказов
- Управление клиентами (CRUD с защитой от удаления)
- Отчёты и статистика
- Экспорт/импорт JSON/XML

### CLI
- `report --period day/week/month` — отчёт
- `export --file` — экспорт в JSON/XML
- `import --file` — импорт из JSON/XML
- `list-customers` — список клиентов
- `add-customer` — добавление клиента
- `list-orders --status` — список заказов

## Технологии

- Python 3.8+
- SQLite / TinyDB
- Tkinter (GUI)
- pytest (тесты)
- argparse (CLI)
- logging (логирование)
