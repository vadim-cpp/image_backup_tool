import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QTextEdit,
                             QFileDialog, QLineEdit, QGroupBox, QFormLayout,
                             QSpinBox, QComboBox, QSystemTrayIcon, QMenu, QAction, QMessageBox)
from PyQt5.QtCore import pyqtSlot, QThread, pyqtSignal, Qt
from PyQt5.QtGui import QIcon
from widgets import SettingsWidget, LogWidget
from scan_worker import ScanWorker


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

    @pyqtSlot()
    def scan_folder(self):
        """Сканирует папку и обрабатывает новые изображения"""
        settings = self.settings_widget.get_settings()

        if not settings['watch_folder']:
            self.log_widget.append_log("Ошибка: Укажите папку для сканирования")
            return

        if not settings['repo_url']:
            self.log_widget.append_log("Ошибка: Укажите URL репозитория")
            return

        # Сохраняем настройки
        self.settings_widget.save_settings()

        # Запускаем сканирование в отдельном потоке
        thread = QThread()
        worker = ScanWorker(settings)
        worker.moveToThread(thread)

        worker.log_signal.connect(self.log_widget.append_log)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        thread.started.connect(worker.scan)
        thread.start()

        # Блокируем кнопку на время сканирования
        self.scan_btn.setEnabled(False)
        thread.finished.connect(lambda: self.scan_btn.setEnabled(True))

        self.log_widget.append_log("Запуск сканирования...")

    @pyqtSlot()
    def restore_backup(self):
        settings = self.settings_widget.get_settings()

        if not settings['repo_url']:
            self.log_widget.append_log("Ошибка: Укажите URL репозитория")
            return

        # Запускаем восстановление в отдельном потоке
        thread = QThread()
        worker = ScanWorker(settings)
        worker.moveToThread(thread)

        worker.log_signal.connect(self.log_widget.append_log)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        thread.started.connect(worker.restore)
        thread.start()

        # Блокируем кнопку на время восстановления
        self.restore_btn.setEnabled(False)
        thread.finished.connect(lambda: self.restore_btn.setEnabled(True))

        self.log_widget.append_log("Запуск восстановления...")