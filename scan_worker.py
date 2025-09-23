import os
import time
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from git_manager import GitManager
from image_processor import ImageProcessor


class ScanWorker(QObject):
    log_signal = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.git_manager = GitManager(settings, self.log_signal)
        self.image_processor = ImageProcessor(settings, self.log_signal)

    @pyqtSlot()
    def scan(self):
        """Сканирует папку и обрабатывает новые изображения"""
        try:
            self.log_signal.emit("Инициализация репозитория...")

            # Инициализируем репозиторий
            if not self.git_manager.init_repo():
                self.log_signal.emit("Ошибка инициализации репозитория")
                self.finished.emit()
                return

            self.log_signal.emit("Начало сканирования папки...")

            # Сканируем папку на наличие изображений
            image_count = self.scan_folder_for_images()

            self.log_signal.emit(f"Сканирование завершено. Обработано изображений: {image_count}")

        except Exception as e:
            self.log_signal.emit(f"Ошибка при сканировании: {str(e)}")
        finally:
            self.finished.emit()

    def scan_folder_for_images(self):
        """Рекурсивно сканирует папку и обрабатывает изображения"""
        image_exts = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp', '.heic')
        processed_count = 0

        watch_folder = self.settings['watch_folder']

        if not os.path.exists(watch_folder):
            self.log_signal.emit(f"Ошибка: Папка {watch_folder} не существует")
            return 0

        for root, dirs, files in os.walk(watch_folder):
            for file in files:
                if file.lower().endswith(image_exts):
                    image_path = os.path.join(root, file)

                    # Проверяем, не является ли файл уже обработанным (имеет _compressed в имени)
                    if '_compressed.' not in file:
                        self.log_signal.emit(f"Найдено изображение: {image_path}")
                        if self.process_image(image_path):
                            processed_count += 1

                        # Небольшая пауза для избежания перегрузки
                        time.sleep(0.1)

        return processed_count

    def process_image(self, image_path):
        """Обрабатывает одно изображение"""
        try:
            # Обрабатываем изображение
            processed_path = self.image_processor.process(image_path)

            if processed_path:
                # Добавляем в git
                self.git_manager.add_to_repo(processed_path)
                return True
            return False

        except Exception as e:
            self.log_signal.emit(f"Ошибка обработки {image_path}: {str(e)}")
            return False

    @pyqtSlot()
    def restore(self):
        """Восстанавливает изображения из репозитория"""
        try:
            self.log_signal.emit("Начало восстановления...")
            if self.git_manager.restore_repo():
                self.log_signal.emit("Восстановление завершено успешно")
            else:
                self.log_signal.emit("Ошибка восстановления")
        except Exception as e:
            self.log_signal.emit(f"Ошибка при восстановлении: {str(e)}")
        finally:
            self.finished.emit()