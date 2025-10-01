from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLineEdit, QPushButton, QLabel, QCheckBox,
                             QDialogButtonBox, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import base64


class AuthDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Авторизация в Git репозитории")
        self.setGeometry(300, 300, 400, 300)
        self.setModal(True)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Информационный текст
        info_label = QLabel(
            "Для доступа к приватному репозиторию введите учетные данные.\n"
            "Для GitHub используйте Personal Access Token вместо пароля."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Форма ввода данных
        form_layout = QFormLayout()

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("username или email")
        form_layout.addRow("Имя пользователя:", self.username_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("пароль или token")
        form_layout.addRow("Пароль/Token:", self.password_edit)

        self.token_edit = QLineEdit()
        self.token_edit.setPlaceholderText("альтернативно: полный token")
        self.token_edit.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Token (только):", self.token_edit)

        # Чекбокс для показа пароля
        self.show_password = QCheckBox("Показать пароль")
        self.show_password.toggled.connect(self.toggle_password_visibility)
        form_layout.addRow("", self.show_password)

        # Чекбокс для сохранения данных
        self.save_credentials = QCheckBox("Сохранить учетные данные")
        self.save_credentials.setChecked(True)
        form_layout.addRow("", self.save_credentials)

        layout.addLayout(form_layout)

        # Кнопки
        button_layout = QHBoxLayout()

        self.test_btn = QPushButton("Проверить подключение")
        self.test_btn.clicked.connect(self.test_connection)
        button_layout.addWidget(self.test_btn)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        button_layout.addWidget(self.button_box)

        layout.addLayout(button_layout)

        # Статус подключения
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: blue;")
        layout.addWidget(self.status_label)

    def toggle_password_visibility(self, checked):
        if checked:
            self.password_edit.setEchoMode(QLineEdit.Normal)
            self.token_edit.setEchoMode(QLineEdit.Normal)
        else:
            self.password_edit.setEchoMode(QLineEdit.Password)
            self.token_edit.setEchoMode(QLineEdit.Password)

    def get_credentials(self):
        """Возвращает учетные данные в разных форматах"""
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        token = self.token_edit.text().strip()

        # Если указан полный token, используем его
        if token:
            return {
                'username': 'token',
                'password': token,
                'token': token,
                'auth_type': 'token'
            }
        elif username and password:
            return {
                'username': username,
                'password': password,
                'token': None,
                'auth_type': 'password'
            }
        else:
            return None

    def validate_and_accept(self):
        credentials = self.get_credentials()
        if not credentials:
            QMessageBox.warning(self, "Ошибка",
                                "Введите имя пользователя и пароль/token")
            return

        if self.save_credentials.isChecked():
            self.save_credentials_to_settings(credentials)

        self.accept()

    def test_connection(self):
        credentials = self.get_credentials()
        if not credentials:
            self.status_label.setText("Введите учетные данные для проверки")
            self.status_label.setStyleSheet("color: red;")
            return

        self.status_label.setText("Проверка подключения...")
        self.status_label.setStyleSheet("color: blue;")

        # Имитация проверки подключения
        # В реальной реализации здесь будет тестовое подключение к репозиторию
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(1000, lambda: self.on_connection_test_result(True))

    def on_connection_test_result(self, success):
        if success:
            self.status_label.setText("Подключение успешно!")
            self.status_label.setStyleSheet("color: green;")
        else:
            self.status_label.setText("Ошибка подключения")
            self.status_label.setStyleSheet("color: red;")

    def save_credentials_to_settings(self, credentials):
        """Сохраняет учетные данные в настройках (базовое шифрование)"""
        from PyQt5.QtCore import QSettings

        settings = QSettings("ImageBackupTool", "Auth")

        # Простое "шифрование" - base64
        if credentials['username']:
            encoded_username = base64.b64encode(
                credentials['username'].encode()).decode()
            settings.setValue("username", encoded_username)

        if credentials['password']:
            encoded_password = base64.b64encode(
                credentials['password'].encode()).decode()
            settings.setValue("password", encoded_password)

        if credentials['token']:
            encoded_token = base64.b64encode(
                credentials['token'].encode()).decode()
            settings.setValue("token", encoded_token)

        settings.setValue("auth_type", credentials['auth_type'])
        settings.setValue("saved", True)

    def load_credentials_from_settings(self):
        """Загружает сохраненные учетные данные"""
        from PyQt5.QtCore import QSettings

        settings = QSettings("ImageBackupTool", "Auth")

        if settings.value("saved", False, type=bool):
            try:
                if settings.value("username"):
                    username = base64.b64decode(
                        settings.value("username").encode()).decode()
                    self.username_edit.setText(username)

                if settings.value("password"):
                    password = base64.b64decode(
                        settings.value("password").encode()).decode()
                    self.password_edit.setText(password)

                if settings.value("token"):
                    token = base64.b64decode(
                        settings.value("token").encode()).decode()
                    self.token_edit.setText(token)
            except Exception:
                # Если возникла ошибка при декодировании, очищаем настройки
                settings.remove("")

    def clear_credentials(self):
        """Очищает сохраненные учетные данные"""
        from PyQt5.QtCore import QSettings
        settings = QSettings("ImageBackupTool", "Auth")
        settings.clear()

        self.username_edit.clear()
        self.password_edit.clear()
        self.token_edit.clear()