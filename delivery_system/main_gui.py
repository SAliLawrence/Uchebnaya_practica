import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, Toplevel, filedialog
from datetime import datetime, timedelta

from database import get_database
from data_export import DataExporter
from logger_config import logger
from models import Order, OrderItem


class DeliveryApp:
    def __init__(self, root, db_type="sqlite"):
        self.root = root
        self.root.title("Быстрая доставка - Система учета заказов")
        self.root.geometry("1300x750")

        self.db = get_database(db_type)
        self.exporter = DataExporter()

        self.setup_ui()
        self.refresh_orders()
        self.check_and_create_test_data()

    def check_and_create_test_data(self):
        customers = self.db.get_all_customers()
        if not customers:
            self.db.add_customer("Иван Петров", "+7 (912) 345-67-89", "г. Москва, ул. Ленина, д.1")
            self.db.add_customer("Мария Иванова", "+7 (913) 456-78-90", "г. Санкт-Петербург, Невский пр., д.10")
            self.db.add_customer("Алексей Сидоров", "+7 (914) 567-89-01", "г. Новосибирск, ул. Советская, д.5")

            items1 = [{"product_name": "Пицца Маргарита", "quantity": 2, "price": 450},
                      {"product_name": "Кола 0.5", "quantity": 2, "price": 100}]
            items2 = [{"product_name": "Суши сет", "quantity": 1, "price": 1200},
                      {"product_name": "Чай зеленый", "quantity": 1, "price": 150}]
            items3 = [{"product_name": "Бургер", "quantity": 3, "price": 350},
                      {"product_name": "Картошка фри", "quantity": 2, "price": 180}]

            self.db.add_order(1, "2025-06-10", "выполнен", 1100, items1)
            self.db.add_order(2, "2025-06-11", "в доставке", 1350, items2)
            self.db.add_order(1, "2025-06-12", "новый", 1410, items3)

            logger.info("Созданы тестовые данные")
            self.refresh_orders()

    def setup_ui(self):
        filter_frame = ttk.LabelFrame(self.root, text="Фильтры", padding=10)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(filter_frame, text="Статус:").grid(row=0, column=0, padx=5, pady=5)
        self.status_filter = ttk.Combobox(filter_frame, values=['Все', 'новый', 'в доставке', 'выполнен', 'отменён'],
                                          width=15)
        self.status_filter.grid(row=0, column=1, padx=5, pady=5)
        self.status_filter.set('Все')

        ttk.Label(filter_frame, text="Дата от (ГГГГ-ММ-ДД):").grid(row=0, column=2, padx=5, pady=5)
        self.date_from = ttk.Entry(filter_frame, width=15)
        self.date_from.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(filter_frame, text="Дата до (ГГГГ-ММ-ДД):").grid(row=0, column=4, padx=5, pady=5)
        self.date_to = ttk.Entry(filter_frame, width=15)
        self.date_to.grid(row=0, column=5, padx=5, pady=5)

        ttk.Button(filter_frame, text="Применить", command=self.refresh_orders).grid(row=0, column=6, padx=10, pady=5)
        ttk.Button(filter_frame, text="Сбросить", command=self.clear_filters).grid(row=0, column=7, padx=5, pady=5)

        actions_frame = ttk.Frame(self.root)
        actions_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(actions_frame, text="Добавить заказ", command=self.add_order).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="Редактировать заказ", command=self.edit_order).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="Удалить заказ", command=self.delete_order).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="Показать отчет", command=self.show_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="Экспорт", command=self.export_orders).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="Импорт", command=self.import_orders).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="Управление клиентами", command=self.manage_customers).pack(side=tk.LEFT, padx=5)

        table_frame = ttk.Frame(self.root)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ('id', 'customer_name', 'order_date', 'status', 'total', 'items_count')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)

        self.tree.heading('id', text='ID')
        self.tree.heading('customer_name', text='Клиент')
        self.tree.heading('order_date', text='Дата')
        self.tree.heading('status', text='Статус')
        self.tree.heading('total', text='Сумма (руб)')
        self.tree.heading('items_count', text='Товаров')

        self.tree.column('id', width=50)
        self.tree.column('customer_name', width=200)
        self.tree.column('order_date', width=120)
        self.tree.column('status', width=120)
        self.tree.column('total', width=120)
        self.tree.column('items_count', width=80)

        v_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.status_bar = ttk.Label(self.root, text="Готово", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def clear_filters(self):
        self.status_filter.set('Все')
        self.date_from.delete(0, tk.END)
        self.date_to.delete(0, tk.END)
        self.refresh_orders()

    def refresh_orders(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        status = self.status_filter.get() if self.status_filter.get() != 'Все' else None
        date_from = self.date_from.get() if self.date_from.get() else None
        date_to = self.date_to.get() if self.date_to.get() else None

        orders = self.db.get_all_orders(status=status)

        if date_from:
            orders = [o for o in orders if o['order_date'] >= date_from]
        if date_to:
            orders = [o for o in orders if o['order_date'] <= date_to]

        for order in orders:
            self.tree.insert('', tk.END, values=(
                order['id'],
                order.get('customer_name', 'Неизвестно'),
                order['order_date'],
                order['status'],
                f"{order['total']:.2f}",
                len(order.get('items', []))
            ))

        self.status_bar.config(text=f"Загружено {len(orders)} заказов")

    def add_order(self):
        dialog = OrderDialog(self.root, self.db, mode="add")
        self.root.wait_window(dialog)
        if dialog.result:
            self.refresh_orders()

    def edit_order(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите заказ для редактирования")
            return

        order_id = self.tree.item(selection[0])['values'][0]
        dialog = OrderDialog(self.root, self.db, mode="edit", order_id=order_id)
        self.root.wait_window(dialog)
        if dialog.result:
            self.refresh_orders()

    def delete_order(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите заказ для удаления")
            return

        if messagebox.askyesno("Подтверждение", "Удалить выбранный заказ?"):
            order_id = self.tree.item(selection[0])['values'][0]
            if self.db.delete_order(order_id):
                messagebox.showinfo("Успех", "Заказ удален")
                self.refresh_orders()
            else:
                messagebox.showerror("Ошибка", "Не удалось удалить заказ")

    def show_report(self):
        report_window = Toplevel(self.root)
        report_window.title("Отчет по заказам")
        report_window.geometry("550x500")

        ttk.Label(report_window, text="Статистика заказов", font=('Arial', 16, 'bold')).pack(pady=15)

        stats_frame = ttk.LabelFrame(report_window, text="Заказы по статусам", padding=10)
        stats_frame.pack(fill=tk.X, padx=20, pady=10)

        status_counts = self.db.get_orders_by_status_count()
        for status, count in status_counts.items():
            ttk.Label(stats_frame, text=f"{status}: {count}").pack(anchor=tk.W, pady=3)

        top_frame = ttk.LabelFrame(report_window, text="Топ-3 клиента по сумме заказов", padding=10)
        top_frame.pack(fill=tk.X, padx=20, pady=10)

        top_customers = self.db.get_top_customers(3)
        for i, customer in enumerate(top_customers, 1):
            ttk.Label(top_frame, text=f"{i}. {customer['name']} - {customer['total_spent']:.2f} руб.").pack(anchor=tk.W,
                                                                                                            pady=3)

        revenue_frame = ttk.LabelFrame(report_window, text="Выручка по периодам", padding=10)
        revenue_frame.pack(fill=tk.X, padx=20, pady=10)

        today = datetime.now().date()

        day_revenue = self.db.get_revenue(today.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))
        week_revenue = self.db.get_revenue((today - timedelta(days=7)).strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))
        month_revenue = self.db.get_revenue((today - timedelta(days=30)).strftime('%Y-%m-%d'),
                                            today.strftime('%Y-%m-%d'))

        ttk.Label(revenue_frame, text=f"За день: {day_revenue:.2f} руб.").pack(anchor=tk.W, pady=3)
        ttk.Label(revenue_frame, text=f"За неделю: {week_revenue:.2f} руб.").pack(anchor=tk.W, pady=3)
        ttk.Label(revenue_frame, text=f"За месяц: {month_revenue:.2f} руб.").pack(anchor=tk.W, pady=3)

        ttk.Button(report_window, text="Закрыть", command=report_window.destroy).pack(pady=20)

    def export_orders(self):
        filename = filedialog.asksaveasfilename(
            filetypes=[('JSON files', '*.json'), ('XML files', '*.xml')],
            defaultextension='.json'
        )

        if filename:
            orders = self.db.get_all_orders()
            if filename.endswith('.json'):
                success = self.exporter.export_to_json(orders, filename)
            elif filename.endswith('.xml'):
                success = self.exporter.export_to_xml(orders, filename)
            else:
                messagebox.showerror("Ошибка", "Неподдерживаемый формат")
                return

            if success:
                messagebox.showinfo("Успех", f"Экспортировано {len(orders)} заказов")

    def import_orders(self):
        filename = filedialog.askopenfilename(filetypes=[('JSON/XML files', '*.json *.xml')])

        if filename:
            if filename.endswith('.json'):
                orders_data = self.exporter.import_from_json(filename)
            elif filename.endswith('.xml'):
                orders_data = self.exporter.import_from_xml(filename)
            else:
                messagebox.showerror("Ошибка", "Неподдерживаемый формат")
                return

            imported = 0
            for order_data in orders_data:
                if self.exporter.validate_order_data(order_data):
                    customer = self.db.get_customer(order_data['customer_id'])
                    if customer:
                        items = [OrderItem.from_dict(item) for item in order_data.get('items', [])]
                        self.db.add_order(
                            customer_id=order_data['customer_id'],
                            order_date=order_data['order_date'],
                            status=order_data['status'],
                            total=order_data['total'],
                            items=[item.to_dict() for item in items]
                        )
                        imported += 1

            messagebox.showinfo("Успех", f"Импортировано {imported} заказов")
            self.refresh_orders()

    def manage_customers(self):
        CustomerDialog(self.root, self.db)


class OrderDialog(Toplevel):
    def __init__(self, parent, db, mode="add", order_id=None):
        super().__init__(parent)
        self.db = db
        self.mode = mode
        self.order_id = order_id
        self.result = False

        self.title(f"{'Редактирование' if mode == 'edit' else 'Добавление'} заказа")
        self.geometry("650x550")

        self.setup_ui()

        if mode == "edit" and order_id:
            self.load_order()

    def setup_ui(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Клиент:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        self.customer_combo = ttk.Combobox(main_frame, width=40, state="readonly")
        self.customer_combo.grid(row=0, column=1, padx=10, pady=10)
        self.load_customers()

        ttk.Label(main_frame, text="Дата (ГГГГ-ММ-ДД):").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        self.date_entry = ttk.Entry(main_frame, width=20)
        self.date_entry.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)
        self.date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))

        ttk.Label(main_frame, text="Статус:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        self.status_combo = ttk.Combobox(main_frame, values=['новый', 'в доставке', 'выполнен', 'отменён'], width=20,
                                         state="readonly")
        self.status_combo.grid(row=2, column=1, padx=10, pady=10, sticky=tk.W)
        self.status_combo.set('новый')

        ttk.Label(main_frame, text="Товары:").grid(row=3, column=0, columnspan=2, pady=10)

        self.items_frame = ttk.Frame(main_frame)
        self.items_frame.grid(row=4, column=0, columnspan=2, padx=10, pady=5)

        self.items = []

        ttk.Button(main_frame, text="+ Добавить товар", command=self.add_item).grid(row=5, column=0, columnspan=2,
                                                                                    pady=10)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=20)

        ttk.Button(btn_frame, text="Сохранить", command=self.save).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Отмена", command=self.destroy).pack(side=tk.LEFT, padx=10)

    def load_customers(self):
        customers = self.db.get_all_customers()
        if not customers:
            messagebox.showwarning("Внимание", "Нет клиентов. Сначала добавьте клиентов")
            self.destroy()
            return
        self.customers = {f"{c['name']} (тел: {c.get('phone', 'не указан')})": c['id'] for c in customers}
        self.customer_combo['values'] = list(self.customers.keys())

    def add_item(self):
        row = len(self.items)
        frame = ttk.Frame(self.items_frame)
        frame.pack(fill=tk.X, pady=2)

        ttk.Label(frame, text=f"{row + 1}.", width=3).pack(side=tk.LEFT, padx=5)

        name_entry = ttk.Entry(frame, width=20)
        name_entry.pack(side=tk.LEFT, padx=5)
        name_entry.insert(0, f"Товар {row + 1}")

        ttk.Label(frame, text="x").pack(side=tk.LEFT)
        qty_entry = ttk.Entry(frame, width=6)
        qty_entry.pack(side=tk.LEFT, padx=5)
        qty_entry.insert(0, "1")

        ttk.Label(frame, text="×").pack(side=tk.LEFT)
        price_entry = ttk.Entry(frame, width=10)
        price_entry.pack(side=tk.LEFT, padx=5)
        price_entry.insert(0, "0")

        ttk.Label(frame, text="руб.").pack(side=tk.LEFT)

        ttk.Button(frame, text="X", command=lambda: self.remove_item(frame), width=3).pack(side=tk.LEFT, padx=10)

        self.items.append((frame, name_entry, qty_entry, price_entry))

    def remove_item(self, frame):
        for i, (f, _, _, _) in enumerate(self.items):
            if f == frame:
                frame.destroy()
                self.items.pop(i)
                break

    def load_order(self):
        order = self.db.get_order(self.order_id)
        if order:
            for key, cust_id in self.customers.items():
                if cust_id == order['customer_id']:
                    self.customer_combo.set(key)
                    break

            self.date_entry.delete(0, tk.END)
            self.date_entry.insert(0, order['order_date'])
            self.status_combo.set(order['status'])

            for idx, item in enumerate(order.get('items', [])):
                frame = ttk.Frame(self.items_frame)
                frame.pack(fill=tk.X, pady=2)

                ttk.Label(frame, text=f"{idx + 1}.", width=3).pack(side=tk.LEFT, padx=5)

                name_entry = ttk.Entry(frame, width=20)
                name_entry.pack(side=tk.LEFT, padx=5)
                name_entry.insert(0, item['product_name'])

                ttk.Label(frame, text="x").pack(side=tk.LEFT)
                qty_entry = ttk.Entry(frame, width=6)
                qty_entry.pack(side=tk.LEFT, padx=5)
                qty_entry.insert(0, str(item['quantity']))

                ttk.Label(frame, text="×").pack(side=tk.LEFT)
                price_entry = ttk.Entry(frame, width=10)
                price_entry.pack(side=tk.LEFT, padx=5)
                price_entry.insert(0, str(item['price']))

                ttk.Label(frame, text="руб.").pack(side=tk.LEFT)

                ttk.Button(frame, text="X", command=lambda: self.remove_item(frame), width=3).pack(side=tk.LEFT,
                                                                                                   padx=10)

                self.items.append((frame, name_entry, qty_entry, price_entry))

    def save(self):
        selected = self.customer_combo.get()
        if not selected:
            messagebox.showerror("Ошибка", "Выберите клиента")
            return

        customer_id = self.customers[selected]

        order_date = self.date_entry.get()
        try:
            datetime.strptime(order_date, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты")
            return

        status = self.status_combo.get()

        items_list = []
        total = 0
        for _, name_entry, qty_entry, price_entry in self.items:
            try:
                product_name = name_entry.get()
                quantity = int(qty_entry.get())
                price = float(price_entry.get())
                items_list.append({'product_name': product_name, 'quantity': quantity, 'price': price})
                total += quantity * price
            except ValueError:
                messagebox.showerror("Ошибка", "Неверный формат количества или цены")
                return

        if not items_list:
            messagebox.showerror("Ошибка", "Добавьте хотя бы один товар")
            return

        if self.mode == "add":
            self.db.add_order(customer_id, order_date, status, total, items_list)
        else:
            self.db.update_order(self.order_id, customer_id, order_date, status, total, items_list)

        self.result = True
        self.destroy()


class CustomerDialog(Toplevel):
    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self.title("Управление клиентами")
        self.geometry("700x500")

        self.setup_ui()
        self.refresh()

    def setup_ui(self):
        form_frame = ttk.LabelFrame(self, text="Добавить нового клиента", padding=15)
        form_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(form_frame, text="Имя:*").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.name_entry = ttk.Entry(form_frame, width=25)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="Телефон:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.phone_entry = ttk.Entry(form_frame, width=25)
        self.phone_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="Адрес:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.address_entry = ttk.Entry(form_frame, width=40)
        self.address_entry.grid(row=2, column=1, columnspan=2, padx=5, pady=5)

        ttk.Button(form_frame, text="Добавить клиента", command=self.add_customer).grid(row=3, column=0, columnspan=2,
                                                                                        pady=10)

        list_frame = ttk.LabelFrame(self, text="Список клиентов", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ('id', 'name', 'phone', 'address')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=12)

        self.tree.heading('id', text='ID')
        self.tree.heading('name', text='Имя')
        self.tree.heading('phone', text='Телефон')
        self.tree.heading('address', text='Адрес')

        self.tree.column('id', width=50)
        self.tree.column('name', width=180)
        self.tree.column('phone', width=130)
        self.tree.column('address', width=280)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(fill=tk.X, pady=10)

        ttk.Button(btn_frame, text="Редактировать", command=self.edit_customer).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Удалить", command=self.delete_customer).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Обновить", command=self.refresh).pack(side=tk.LEFT, padx=5)

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        customers = self.db.get_all_customers()
        for customer in customers:
            self.tree.insert('', tk.END, values=(
                customer['id'],
                customer['name'],
                customer.get('phone', ''),
                customer.get('address', '')
            ))

    def add_customer(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Ошибка", "Введите имя клиента")
            return

        self.db.add_customer(name, self.phone_entry.get().strip(), self.address_entry.get().strip())
        self.name_entry.delete(0, tk.END)
        self.phone_entry.delete(0, tk.END)
        self.address_entry.delete(0, tk.END)
        self.refresh()

    def edit_customer(self):
        selection = self.tree.selection()
        if not selection:
            return

        values = self.tree.item(selection[0])['values']
        customer_id = values[0]

        new_name = simpledialog.askstring("Редактирование", "Новое имя:", initialvalue=values[1])
        if new_name:
            new_phone = simpledialog.askstring("Редактирование", "Новый телефон:", initialvalue=values[2])
            new_address = simpledialog.askstring("Редактирование", "Новый адрес:", initialvalue=values[3])
            self.db.update_customer(customer_id, new_name, new_phone or '', new_address or '')
            self.refresh()

    def delete_customer(self):
        selection = self.tree.selection()
        if not selection:
            return

        values = self.tree.item(selection[0])['values']
        customer_id = values[0]

        if messagebox.askyesno("Подтверждение", f"Удалить клиента '{values[1]}'?"):
            if self.db.delete_customer(customer_id):
                self.refresh()
            else:
                messagebox.showerror("Ошибка", "Нельзя удалить клиента с заказами")


if __name__ == '__main__':
    root = tk.Tk()
    app = DeliveryApp(root)
    root.mainloop()
