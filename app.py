import traceback
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QTextEdit,
                             QFileDialog, QLineEdit, QGroupBox, QFormLayout,
                             QSpinBox, QComboBox, QSystemTrayIcon, QMenu, QAction, QMessageBox, QDialog)
from PyQt5.QtCore import pyqtSlot, QThread, pyqtSignal, Qt
from PyQt5.QtGui import QIcon

from auth_dialog import AuthDialog
from widgets import SettingsWidget, LogWidget
from scan_worker import ScanWorker
from selection_dialog import FileSelectionDialog


class ImageBackupApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.setApplicationName("Image Backup Tool")
        self.setApplicationVersion("1.0")

        self.main_window = MainWindow()

    def run(self):
        self.main_window.show()
        return self.exec_()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Backup Tool")
        self.setGeometry(100, 100, 800, 600)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Основной layout
        layout = QVBoxLayout(central_widget)

        # Виджет настроек
        self.settings_widget = SettingsWidget()
        layout.addWidget(self.settings_widget)

        # Виджет лога
        self.log_widget = LogWidget()
        layout.addWidget(self.log_widget)

        # Кнопки управления
        button_layout = QHBoxLayout()

        self.scan_btn = QPushButton("Сканировать")
        self.scan_btn.clicked.connect(self.scan_folder)
        button_layout.addWidget(self.scan_btn)

        self.restore_btn = QPushButton("Восстановить")
        self.restore_btn.clicked.connect(self.restore_backup)
        button_layout.addWidget(self.restore_btn)

        layout.addLayout(button_layout)

        # Загрузка настроек
        self.settings_widget.load_settings()

        auth_layout = QHBoxLayout()
        self.auth_btn = QPushButton("Настройки авторизации")
        self.auth_btn.clicked.connect(self.show_auth_dialog)
        auth_layout.addWidget(self.auth_btn)
        auth_layout.addStretch()

        layout.addLayout(auth_layout)

        # Ссылки на потоки и воркеры
        self.scan_thread = None
        self.scan_worker = None
        self.commit_thread = None
        self.commit_worker = None
        self.restore_thread = None
        self.restore_worker = None

    @pyqtSlot()
    def show_auth_dialog(self):
        """Показывает диалог авторизации"""
        try:
            dialog = AuthDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                self.log_widget.append_log("Учетные данные сохранены")
        except Exception as e:
            self.log_widget.append_log(f"Ошибка в диалоге авторизации: {str(e)}")

    @pyqtSlot()
    def scan_folder(self):
        """Сканирует папку и показывает диалог выбора файлов"""
        try:
            settings = self.settings_widget.get_settings()

            if not settings['watch_folder']:
                self.log_widget.append_log("Ошибка: Укажите папку для сканирования")
                return

            if not settings['repo_url']:
                self.log_widget.append_log("Ошибка: Укажите URL репозитория")
                return

            # Сохраняем настройки
            self.settings_widget.save_settings()

            # Останавливаем предыдущий поток, если он есть
            if self.scan_thread and self.scan_thread.isRunning():
                self.scan_thread.quit()
                self.scan_thread.wait()

            # Запускаем сканирование в отдельном потоке
            self.scan_thread = QThread()
            self.scan_worker = ScanWorker(settings)
            self.scan_worker.moveToThread(self.scan_thread)

            self.scan_worker.log_signal.connect(self.log_widget.append_log)
            self.scan_worker.files_found.connect(self.on_files_found)
            self.scan_worker.finished.connect(self.on_scan_finished)
            # Добавляем обработчик для запроса аутентификации
            self.scan_worker.auth_required.connect(self.handle_auth_required)

            self.scan_thread.started.connect(self.scan_worker.scan)
            self.scan_thread.start()

            # Блокируем кнопку на время сканирования
            self.scan_btn.setEnabled(False)
            self.log_widget.append_log("Запуск сканирования...")

        except Exception as e:
            self.log_widget.append_log(f"Ошибка при запуске сканирования: {str(e)}")
            self.log_widget.append_log(traceback.format_exc())

    def handle_auth_required(self):
        """Обрабатывает запрос на аутентификацию"""
        self.log_widget.append_log("Требуется аутентификация для доступа к репозиторию")
        self.show_auth_dialog()

    @pyqtSlot()
    def on_scan_finished(self):
        """Вызывается при завершении сканирования"""
        self.scan_btn.setEnabled(True)
        if self.scan_thread:
            self.scan_thread.quit()
            self.scan_thread.wait()
        self.scan_thread = None
        self.scan_worker = None

    @pyqtSlot(list)
    def on_files_found(self, file_list):
        """Обрабатывает найденные файлы и показывает диалог выбора"""
        try:
            if not file_list:
                self.log_widget.append_log("Новых изображений не найдено")
                return

            # Показываем диалог выбора файлов в главном потоке
            dialog = FileSelectionDialog(file_list, self)
            if dialog.exec_() == QDialog.Accepted:
                selected_files = dialog.get_selected_files()
                if selected_files:
                    self.log_widget.append_log(f"Выбрано файлов для фиксации: {len(selected_files)}")
                    self.commit_files(selected_files)
                else:
                    self.log_widget.append_log("Не выбрано ни одного файла")
            else:
                self.log_widget.append_log("Отменено пользователем")

        except Exception as e:
            self.log_widget.append_log(f"Ошибка при выборе файлов: {str(e)}")
            self.log_widget.append_log(traceback.format_exc())

    def commit_files(self, file_list):
        """Фиксирует выбранные файлы в репозитории"""
        try:
            settings = self.settings_widget.get_settings()

            # Останавливаем предыдущий поток, если он есть
            if self.commit_thread and self.commit_thread.isRunning():
                self.commit_thread.quit()
                self.commit_thread.wait()

            # Запускаем фиксацию в отдельном потоке
            self.commit_thread = QThread()
            self.commit_worker = ScanWorker(settings)
            self.commit_worker.moveToThread(self.commit_thread)

            self.commit_worker.log_signal.connect(self.log_widget.append_log)
            self.commit_worker.finished.connect(self.on_commit_finished)

            # Передаем список файлов для фиксации
            self.commit_worker.set_files_to_commit(file_list)
            self.commit_thread.started.connect(self.commit_worker.commit_files)
            self.commit_thread.start()

            self.log_widget.append_log("Запуск фиксации файлов...")

        except Exception as e:
            self.log_widget.append_log(f"Ошибка при запуске фиксации: {str(e)}")
            self.log_widget.append_log(traceback.format_exc())

    @pyqtSlot()
    def on_commit_finished(self):
        """Вызывается при завершении фиксации"""
        if self.commit_thread:
            self.commit_thread.quit()
            self.commit_thread.wait()
        self.commit_thread = None
        self.commit_worker = None

    @pyqtSlot()
    def restore_backup(self):
        """Восстанавливает изображения из репозитория"""
        try:
            settings = self.settings_widget.get_settings()

            if not settings['repo_url']:
                self.log_widget.append_log("Ошибка: Укажите URL репозитория")
                return

            # Останавливаем предыдущий поток, если он есть
            if self.restore_thread and self.restore_thread.isRunning():
                self.restore_thread.quit()
                self.restore_thread.wait()

            # Запускаем восстановление в отдельном потоке
            self.restore_thread = QThread()
            self.restore_worker = ScanWorker(settings)
            self.restore_worker.moveToThread(self.restore_thread)

            self.restore_worker.log_signal.connect(self.log_widget.append_log)
            self.restore_worker.finished.connect(self.on_restore_finished)

            self.restore_thread.started.connect(self.restore_worker.restore)
            self.restore_thread.start()

            # Блокируем кнопку на время восстановления
            self.restore_btn.setEnabled(False)
            self.log_widget.append_log("Запуск восстановления...")

        except Exception as e:
            self.log_widget.append_log(f"Ошибка при запуске восстановления: {str(e)}")
            self.log_widget.append_log(traceback.format_exc())

    @pyqtSlot()
    def on_restore_finished(self):
        """Вызывается при завершении восстановления"""
        self.restore_btn.setEnabled(True)
        if self.restore_thread:
            self.restore_thread.quit()
            self.restore_thread.wait()
        self.restore_thread = None
        self.restore_worker = None