from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QFormLayout, QLineEdit, QPushButton, QLabel,
                             QSpinBox, QComboBox, QTextEdit, QFileDialog, QCheckBox)
from PyQt5.QtCore import QSettings, QDateTime


class SettingsWidget(QGroupBox):
    def __init__(self):
        super().__init__("Настройки")

        layout = QFormLayout()
        self.setLayout(layout)

        # Поле для выбора папки
        self.folder_layout = QHBoxLayout()
        self.folder_edit = QLineEdit()
        self.folder_btn = QPushButton("Обзор...")
        self.folder_btn.clicked.connect(self.select_folder)
        self.folder_layout.addWidget(self.folder_edit)
        self.folder_layout.addWidget(self.folder_btn)
        layout.addRow("Папка для сканирования:", self.folder_layout)

        # Поле для URL репозитория
        self.repo_edit = QLineEdit()
        self.repo_edit.setPlaceholderText("https://github.com/username/repository.git")
        layout.addRow("URL Git репозитория:", self.repo_edit)

        # Настройки сжатия
        self.format_combo = QComboBox()
        self.format_combo.addItems(["webp", "jpeg", "avif"])
        layout.addRow("Формат сжатия:", self.format_combo)

        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(85)
        self.quality_spin.setSuffix("%")
        layout.addRow("Качество сжатия:", self.quality_spin)

        # Максимальный размер
        self.resize_check = QCheckBox("Изменять размер изображений")
        layout.addRow(self.resize_check)

        self.max_size_spin = QSpinBox()
        self.max_size_spin.setRange(100, 10000)
        self.max_size_spin.setValue(1920)
        self.max_size_spin.setSuffix("px")
        self.max_size_spin.setEnabled(False)
        self.resize_check.toggled.connect(self.max_size_spin.setEnabled)
        layout.addRow("Максимальный размер:", self.max_size_spin)

        # Загрузка настроек
        self.load_settings()

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку для сканирования")
        if folder:
            self.folder_edit.setText(folder)

    def get_settings(self):
        return {
            'watch_folder': self.folder_edit.text(),
            'repo_url': self.repo_edit.text(),
            'compression_format': self.format_combo.currentText().lower(),
            'compression_quality': self.quality_spin.value(),
            'resize_enabled': self.resize_check.isChecked(),
            'max_size': self.max_size_spin.value()
        }

    def load_settings(self):
        settings = QSettings("ImageBackupTool", "Settings")
        self.folder_edit.setText(settings.value("watch_folder", ""))
        self.repo_edit.setText(settings.value("repo_url", ""))
        self.format_combo.setCurrentText(settings.value("compression_format", "webp"))
        self.quality_spin.setValue(int(settings.value("compression_quality", 85)))
        self.resize_check.setChecked(settings.value("resize_enabled", False, type=bool))
        self.max_size_spin.setValue(int(settings.value("max_size", 1920)))

    def save_settings(self):
        settings = QSettings("ImageBackupTool", "Settings")
        current_settings = self.get_settings()
        for key, value in current_settings.items():
            settings.setValue(key, value)


class LogWidget(QGroupBox):
    def __init__(self):
        super().__init__("Лог выполнения")

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        layout.addWidget(self.log_text)

    def append_log(self, message):
        self.log_text.append(f"{QDateTime.currentDateTime().toString('hh:mm:ss')}: {message}")