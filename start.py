import sys
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QPixmap, QIntValidator
from PyQt6.QtCore import Qt, QTimer, QSize
import psycopg2

# Класс для окна входа
class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Вход в систему")
        self.resize(400, 200)

        self.layout = QVBoxLayout()
        self.stacked_widget = QStackedWidget(self)

        # Создание страницы входа
        self.login_page = QWidget()
        self.login_layout = QVBoxLayout()

        self.username_input = QLineEdit(self)
        self.username_input.setPlaceholderText("Логин")
        self.login_layout.addWidget(self.username_input)

        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_layout.addWidget(self.password_input)

        self.error_label = QLabel("", self)
        self.error_label.setStyleSheet("color: red;")
        self.login_layout.addWidget(self.error_label)

        self.login_button = QPushButton("Войти", self)
        self.login_button.clicked.connect(self.check_credentials)
        self.login_layout.addWidget(self.login_button)

        self.login_page.setLayout(self.login_layout)

        # Добавляем страницу входа в QStackedWidget
        self.stacked_widget.addWidget(self.login_page)
        self.layout.addWidget(self.stacked_widget)
        self.setLayout(self.layout)

    def check_credentials(self):
        username = self.username_input.text()
        password = self.password_input.text()
        self.error_label.setText("")  # Очистить предыдущее сообщение об ошибке

        try:
            connection = psycopg2.connect(
                dbname="ZOO store",
                user="postgres",
                password="Pelmeshka257",
                host="localhost"
            )
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM Сотрудники WHERE Логин = %s AND Пароль = %s", (username, password))
            result = cursor.fetchone()

            if result:
                self.close()  # Закрыть окно входа
                self.main_window = MainWindow()  # Открыть главное окно
                self.main_window.show()
            else:
                self.show_error_message("Неверный логин или пароль.")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
        finally:
            if connection:
                cursor.close()
                connection.close()

    def show_error_message(self, message):
        self.error_label.setText(message)
        QTimer.singleShot(5000, self.clear_error_message)

    def clear_error_message(self):
        self.error_label.setText("")

# Класс для главного окна с каталогами и товарами
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Категории и Подкатегории из PostgreSQL")
        self.resize(1200, 800)

        self.conn = psycopg2.connect(
            dbname="ZOO store",
            user="postgres",
            password="Pelmeshka257",
            host="localhost"
        )
        self.cursor = self.conn.cursor()

        # Атрибут для отслеживания состояния раскрытия категорий
        self.expanded_categories = {}

        # Корзина для хранения добавленных товаров
        self.cart = []

        # Словарь для хранения количества товаров в корзине
        self.cart_quantities = {}

        # Основной виджет и макет
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Кнопки для переключения между виджетами
        self.button_layout = QHBoxLayout()
        self.button1 = QPushButton("Виджет 1")
        self.button2 = QPushButton("Виджет 2")
        self.button3 = QPushButton("Виджет 3")
        self.button4 = QPushButton("Виджет 4")

        # Подключение кнопок к слотам
        self.button1.clicked.connect(lambda: self.switch_widget(0))
        self.button2.clicked.connect(lambda: self.switch_widget(1))
        self.button3.clicked.connect(lambda: self.switch_widget(2))
        self.button4.clicked.connect(lambda: self.switch_widget(3))

        # Добавление кнопок в горизонтальный макет
        self.button_layout.addWidget(self.button1)
        self.button_layout.addWidget(self.button2)
        self.button_layout.addWidget(self.button3)
        self.button_layout.addWidget(self.button4)

        # Добавление кнопок в основной макет
        self.layout.addLayout(self.button_layout)

        # Создание QStackedWidget для управления виджетами
        self.stacked_widget = QStackedWidget()
        self.layout.addWidget(self.stacked_widget)

        # Подключение события currentChanged
        self.stacked_widget.currentChanged.connect(self.on_widget_changed)

        # Создание виджетов
        self.create_widgets()

    def create_widgets(self):
        # Виджет 1: Категории и подкатегории
        self.widget1 = QWidget()
        self.widget1_layout = QHBoxLayout(self.widget1)

        # Список категорий
        self.list_widget = QListWidget()
        self.list_widget.setFixedWidth(200)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.widget1_layout.addWidget(self.list_widget)

        # Область с прокруткой для товаров
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QGridLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)
        self.widget1_layout.addWidget(self.scroll_area)

        # Загрузка категорий
        self.load_categories()

        # Подключение события клика
        self.list_widget.itemClicked.connect(self.on_item_clicked)

        # Виджет 2: Корзина
        self.widget2 = QWidget()
        self.widget2_layout = QVBoxLayout(self.widget2)

        # Область с прокруткой для товаров в корзине
        self.cart_scroll_area = QScrollArea()
        self.cart_scroll_area.setWidgetResizable(True)
        self.cart_scroll_content = QWidget()
        self.cart_scroll_layout = QGridLayout(self.cart_scroll_content)
        self.cart_scroll_area.setWidget(self.cart_scroll_content)
        self.widget2_layout.addWidget(self.cart_scroll_area)

        # Кнопка "Отменить заказ"
        self.cancel_order_button = QPushButton("Отменить заказ")
        self.cancel_order_button.clicked.connect(self.cancel_order)
        self.widget2_layout.addWidget(self.cancel_order_button)

        # Кнопка "Оформить заказ"
        self.place_order_button = QPushButton("Оформить заказ")
        self.place_order_button.clicked.connect(self.place_order)
        self.widget2_layout.addWidget(self.place_order_button)

        # Виджет 3: Пустой виджет
        self.widget3 = QLabel("Это Виджет 3")
        self.widget3.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Виджет 4: Пустой виджет
        self.widget4 = QLabel("Это Виджет 4")
        self.widget4.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Добавление виджетов в QStackedWidget
        self.stacked_widget.addWidget(self.widget1)
        self.stacked_widget.addWidget(self.widget2)
        self.stacked_widget.addWidget(self.widget3)
        self.stacked_widget.addWidget(self.widget4)

        # Установка начального виджета (Виджет 1)
        self.stacked_widget.setCurrentIndex(0)

    def switch_widget(self, index):
        # Переключение на выбранный виджет
        self.stacked_widget.setCurrentIndex(index)

    def on_widget_changed(self, index):
        if index == 1:  # Если активен виджет 2
            self.update_cart_widget()

    def load_categories(self):
        try:
            self.cursor.execute("SELECT id_категории, Название FROM Категории")
            self.categories = self.cursor.fetchall()

            for category in self.categories:
                item = QListWidgetItem(category[1])
                item.setData(1, category[0])
                self.list_widget.addItem(item)
                self.expanded_categories[category[0]] = False
        except Exception as e:
            print(f"Ошибка при загрузке категорий: {e}")

    def on_item_clicked(self, item):
        if not item.text().startswith("    "):
            category_id = item.data(1)
            if not self.is_expanded(category_id):
                self.expand_item(item, category_id)
            else:
                self.collapse_item(item)
        else:
            self.load_products_for_subcategory(item.text().strip())

    def expand_item(self, item, category_id):
        try:
            self.cursor.execute("SELECT Название FROM Подкатегории WHERE id_категории = %s", (category_id,))
            subcategories = self.cursor.fetchall()

            for subcategory in subcategories:
                sub_item = QListWidgetItem("            " + subcategory[0])
                self.list_widget.insertItem(self.list_widget.row(item) + 1, sub_item)

            self.expanded_categories[category_id] = True
        except Exception as e:
            print(f"Ошибка при раскрытии подкатегории: {e}")

    def collapse_item(self, item):
        row = self.list_widget.row(item)
        while True:
            next_item = self.list_widget.item(row + 1)
            if next_item and next_item.text().startswith("   "):
                self.list_widget.takeItem(row + 1)
            else:
                break

        self.expanded_categories[item.data(1)] = False

    def is_expanded(self, category_id):
        return self.expanded_categories.get(category_id, False)

    def load_products_for_subcategory(self, subcategory_name):
        try:
            # Очистка предыдущих карточек
            for i in reversed(range(self.scroll_layout.count())):
                self.scroll_layout.itemAt(i).widget().setParent(None)

            # Загрузка товаров для выбранной подкатегории
            self.cursor.execute(
                "SELECT Название, Количество, Цена, Фото FROM Товары WHERE id_подкатегории = (SELECT id_подкатегории FROM Подкатегории WHERE Название = %s)",
                (subcategory_name,)
            )
            products = self.cursor.fetchall()

            # Создание карточек для каждого товара
            self.update_product_cards(products)

        except Exception as e:
            print(f"Ошибка при загрузке товаров: {e}")

    def update_product_cards(self, products):
        # Очистка предыдущих карточек
        for i in reversed(range(self.scroll_layout.count())):
            self.scroll_layout.itemAt(i).widget().setParent(None)

        card_width = 200
        # Ширина области прокрутки
        scroll_width = self.scroll_area.width()
        # Количество карточек в строке
        cards_per_row = max(1, scroll_width // card_width)

        # Создание карточек для каждого товара
        row, col = 0, 0
        for product in products:
            card = self.create_product_card(product)
            self.scroll_layout.addWidget(card, row, col)

            # Переход на следующую колонку
            col += 1
            # Если достигнута граница окна, переходим на новую строку
            if col >= cards_per_row:
                col = 0
                row += 1

    def create_product_card(self, product):
        # Создание рамки для товара
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setLineWidth(2)
        card.setFixedSize(200, 350)  # Фиксированные размеры карточки
        card_layout = QVBoxLayout(card)  # Вертикальный макет

        # Изображение товара
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if product[3]:  # Если путь к изображению указан
            try:
                pixmap = QPixmap(product[3])
                if not pixmap.isNull():
                    image_label.setPixmap(pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio))
                else:
                    image_label.setText("Изображение\nне найдено")
                    image_label.setStyleSheet("color: gray; font-size: 12px;")
            except Exception as e:
                print(f"Ошибка при загрузке изображения: {e}")
                image_label.setText("Ошибка\nзагрузки")
                image_label.setStyleSheet("color: red; font-size: 12px;")
        else:
            image_label.setText("Нет\nизображения")
            image_label.setStyleSheet("color: gray; font-size: 12px;")

        card_layout.addWidget(image_label)

        # Название товара
        name_label = QLabel(f"Название: {product[0]}")
        name_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setWordWrap(True)
        card_layout.addWidget(name_label)

        # Количество товара
        quantity_label = QLabel(f"Количество: {product[1]}")
        quantity_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(quantity_label)

        # Цена товара
        try:
            price_str = product[2].replace("?", "").replace(",", ".")
            price = float(price_str)
            formatted_price = f"{price:.2f} ₽"
        except (ValueError, AttributeError) as e:
            print(f"Ошибка при обработке цены: {e}")
            formatted_price = "Цена не указана"

        price_label = QLabel(f"Цена: {formatted_price}")
        price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(price_label)

        # Кнопка "Добавить"
        add_button = QPushButton("Добавить")
        add_button.clicked.connect(lambda: self.add_to_cart(product))
        card_layout.addWidget(add_button)

        return card

    def add_to_cart(self, product):
        # Проверяем, есть ли товар уже в корзине
        if product not in self.cart:
            self.cart.append(product)  # Добавляем товар в корзину, если его там нет
            self.cart_quantities[product] = 1  # Устанавливаем начальное количество
            self.update_cart_widget()  # Обновляем виджет корзины

    def update_cart_widget(self):
        # Очистка предыдущих карточек в корзине
        for i in reversed(range(self.cart_scroll_layout.count())):
            widget = self.cart_scroll_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)  # Удаляем виджет из макета

        # Обновляем расположение карточек в корзине
        self.update_cart_product_cards()

    def update_cart_product_cards(self):
        card_width = 200
        # Ширина области прокрутки
        scroll_width = self.cart_scroll_area.width()
        # Количество карточек в строке
        cards_per_row = max(1, scroll_width // card_width)

        # Создание карточек для каждого товара в корзине
        row, col = 0, 0
        for product in self.cart:
            card = self.create_cart_product_card(product)
            self.cart_scroll_layout.addWidget(card, row, col)

            # Переход на следующую колонку
            col += 1
            # Если достигнута граница окна, переходим на новую строку
            if col >= cards_per_row:
                col = 0
                row += 1

    def create_cart_product_card(self, product):
        # Создание рамки для товара в корзине
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setLineWidth(2)
        card.setFixedSize(200, 350)
        card_layout = QVBoxLayout(card)  # Вертикальное расположение

        # Изображение товара
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if product[3]:  # Если путь к изображению указан
            try:
                pixmap = QPixmap(product[3])
                if not pixmap.isNull():
                    image_label.setPixmap(pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio))
                else:
                    image_label.setText("Изображение\nне найдено")
                    image_label.setStyleSheet("color: gray; font-size: 12px;")
            except Exception as e:
                print(f"Ошибка при загрузке изображения: {e}")
                image_label.setText("Ошибка\nзагрузки")
                image_label.setStyleSheet("color: red; font-size: 12px;")
        else:
            image_label.setText("Нет\nизображения")
            image_label.setStyleSheet("color: gray; font-size: 12px;")

        card_layout.addWidget(image_label)

        # Название товара
        name_label = QLabel(f"Название: {product[0]}")
        name_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setWordWrap(True)
        card_layout.addWidget(name_label)

        # Горизонтальный макет для кнопок и поля ввода количества
        quantity_layout = QHBoxLayout()

        # Кнопка "-"
        minus_button = QPushButton("-")
        minus_button.setFixedSize(30, 30)  # Фиксированный размер кнопки
        minus_button.clicked.connect(lambda: self.update_quantity(product, -1))
        quantity_layout.addWidget(minus_button)

        # Поле для ввода количества
        quantity_input = QLineEdit()
        quantity_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        quantity_input.setFixedSize(50, 30)  # Фиксированный размер поля
        quantity_input.setText(str(self.cart_quantities.get(product, 1)))  # Устанавливаем сохраненное количество
        quantity_input.setValidator(QIntValidator(1, product[1]))  # Ограничение ввода
        quantity_input.textChanged.connect(lambda: self.validate_quantity(product, quantity_input))
        quantity_layout.addWidget(quantity_input)

        # Кнопка "+"
        plus_button = QPushButton("+")
        plus_button.setFixedSize(30, 30)  # Фиксированный размер кнопки
        plus_button.clicked.connect(lambda: self.update_quantity(product, 1))
        quantity_layout.addWidget(plus_button)

        card_layout.addLayout(quantity_layout)

        # Кнопка "Удалить"
        delete_button = QPushButton("Удалить")
        delete_button.clicked.connect(lambda: self.remove_from_cart(product))
        card_layout.addWidget(delete_button)

        return card

    def update_quantity(self, product, delta):
        # Получаем текущее количество
        current_quantity = self.cart_quantities.get(product, 1)
        # Вычисляем новое количество с учетом ограничений
        new_quantity = max(1, min(product[1], current_quantity + delta))
        # Обновляем значение в словаре
        self.cart_quantities[product] = new_quantity
        # Обновляем значение в поле ввода
        self.update_cart_widget()

    def validate_quantity(self, product, quantity_input):
        # Получаем введенное значение
        try:
            quantity = int(quantity_input.text())
        except ValueError:
            quantity = 1  # Если введено не число, устанавливаем значение по умолчанию

        # Ограничиваем макс. кол-во товаров, которое указано в бд
        if quantity > product[1]:
            quantity_input.setText(str(product[1]))
            quantity = product[1]
        elif quantity < 1:
            quantity_input.setText("1")
            quantity = 1

        # Обновляем значение в словаре
        self.cart_quantities[product] = quantity

    def remove_from_cart(self, product):
        # Удаляем товар из корзины и из словаря количества
        if product in self.cart:
            self.cart.remove(product)
            if product in self.cart_quantities:
                del self.cart_quantities[product]
            # Обновляем виджет корзины
            self.update_cart_widget()

    def cancel_order(self):
        # Отмена заказа
        self.cart = []
        self.cart_quantities = {}
        self.update_cart_widget()

    def place_order(self):
        # Кнопка для оформления заказа (пока ничего не делает)
        QMessageBox.information(self, "Оформление заказа", "Заказ оформлен!")

    def resizeEvent(self, event):
        # При изменении размера окна обновляем расположение карточек
        super().resizeEvent(event)
        if self.stacked_widget.currentIndex() == 0:  # Если активен виджет 1
            self.update_product_cards(self.get_current_products())
        elif self.stacked_widget.currentIndex() == 1:  # Если активен виджет 2 (корзина)
            self.update_cart_widget()  # Обновляем корзину

    def get_current_products(self):
        # Получаем текущие товары для отображения
        try:
            current_item = self.list_widget.currentItem()
            if current_item and current_item.text().startswith("    "):
                subcategory_name = current_item.text().strip()
                self.cursor.execute(
                    "SELECT Название, Количество, Цена, Фото FROM Товары WHERE id_подкатегории = (SELECT id_подкатегории FROM Подкатегории WHERE Название = %s)",
                    (subcategory_name,)
                )
                return self.cursor.fetchall()
        except Exception as e:
            print(f"Ошибка при загрузке товаров: {e}")
        return []

    def closeEvent(self, event):
        self.cursor.close()
        self.conn.close()

# Запуск приложения
if __name__ == "__main__":
    app = QApplication(sys.argv)
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec())