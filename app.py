import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QTextEdit,
                             QFileDialog, QLineEdit, QGroupBox, QFormLayout,
                             QSpinBox, QComboBox, QSystemTrayIcon, QMenu, QAction, QMessageBox)
from PyQt5.QtCore import pyqtSlot, QThread, pyqtSignal, Qt
from PyQt5.QtGui import QIcon
from widgets import SettingsWidget, LogWidget
from backup_worker import BackupWorker


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

        self.start_btn = QPushButton("Старт")
        self.start_btn.clicked.connect(self.start_backup)
        button_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Стоп")
        self.stop_btn.clicked.connect(self.stop_backup)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)

        self.restore_btn = QPushButton("Восстановить")
        self.restore_btn.clicked.connect(self.restore_backup)
        button_layout.addWidget(self.restore_btn)

        layout.addLayout(button_layout)

        # Инициализация worker и потока
        self.backup_worker = None
        self.thread = None

        # Загрузка настроек
        self.settings_widget.load_settings()

    @pyqtSlot()
    def start_backup(self):
        # Получаем настройки
        settings = self.settings_widget.get_settings()

        # Проверяем обязательные поля
        if not settings['watch_folder'] or not settings['repo_url']:
            self.log_widget.append_log("Ошибка: Укажите папку для наблюдения и URL репозитория")
            return

        # Сохраняем настройки
        self.settings_widget.save_settings()

        # Создаем и запускаем worker в отдельном потоке
        self.thread = QThread()
        self.backup_worker = BackupWorker(settings)
        self.backup_worker.moveToThread(self.thread)

        # Подключаем сигналы
        self.backup_worker.log_signal.connect(self.log_widget.append_log)
        self.backup_worker.finished.connect(self.on_worker_finished)
        self.thread.started.connect(self.backup_worker.run)

        # Меняем состояние UI
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.settings_widget.setEnabled(False)

        # Запускаем поток
        self.thread.start()

        self.log_widget.append_log("Запуск мониторинга...")

    @pyqtSlot()
    def stop_backup(self):
        if self.backup_worker:
            self.backup_worker.stop()
            self.log_widget.append_log("Остановка мониторинга...")

    @pyqtSlot()
    def on_worker_finished(self):
        if self.thread:
            self.thread.quit()
            self.thread.wait()

        # Восстанавливаем состояние UI
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.settings_widget.setEnabled(True)

        self.log_widget.append_log("Мониторинг остановлен")

    @pyqtSlot()
    def restore_backup(self):
        settings = self.settings_widget.get_settings()

        if not settings['repo_url']:
            self.log_widget.append_log("Ошибка: Укажите URL репозитория")
            return

        # Запускаем восстановление в отдельном потоке
        thread = QThread()
        worker = BackupWorker(settings)
        worker.moveToThread(thread)

        worker.log_signal.connect(self.log_widget.append_log)
        worker.finished.connect(thread.quit)

        thread.started.connect(worker.restore)
        thread.start()

        self.log_widget.append_log("Запуск восстановления...")