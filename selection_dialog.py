from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
                             QListWidgetItem, QPushButton, QLabel,
                             QDialogButtonBox)
from PyQt5.QtCore import Qt


class FileSelectionDialog(QDialog):
    def __init__(self, file_list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Выбор файлов для фиксации")
        self.setGeometry(200, 200, 600, 400)

        layout = QVBoxLayout(self)

        # Заголовок
        title_label = QLabel("Найдены новые изображения. Выберите файлы для фиксации:")
        layout.addWidget(title_label)

        # Список файлов с чекбоксами
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        # Заполняем список
        for file_path in file_list:
            item = QListWidgetItem(file_path)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            self.list_widget.addItem(item)

        # Кнопки выбора всех/ничего
        button_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("Выбрать все")
        self.select_none_btn = QPushButton("Снять все")
        button_layout.addWidget(self.select_all_btn)
        button_layout.addWidget(self.select_none_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Стандартные кнопки диалога
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        # Подключаем сигналы
        self.select_all_btn.clicked.connect(self.select_all)
        self.select_none_btn.clicked.connect(self.select_none)

    def select_all(self):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setCheckState(Qt.Checked)

    def select_none(self):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setCheckState(Qt.Unchecked)

    def get_selected_files(self):
        selected_files = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.Checked:
                selected_files.append(item.text())
        return selected_files