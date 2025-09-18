import os
import time
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from git_manager import GitManager
from image_processor import ImageProcessor


class BackupWorker(QObject):
    log_signal = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.is_running = False
        self.observer = None
        self.git_manager = GitManager(settings, self.log_signal)
        self.image_processor = ImageProcessor(settings, self.log_signal)

    @pyqtSlot()
    def run(self):
        try:
            self.is_running = True
            self.log_signal.emit("Инициализация репозитория...")

            # Инициализируем репозиторий
            if not self.git_manager.init_repo():
                self.log_signal.emit("Ошибка инициализации репозитория")
                self.finished.emit()
                return

            # Создаем наблюдатель за файловой системой
            event_handler = ImageEventHandler(self)
            self.observer = Observer()
            self.observer.schedule(event_handler, self.settings['watch_folder'], recursive=True)
            self.observer.start()

            self.log_signal.emit("Мониторинг запущен")

            # Главный цикл
            while self.is_running:
                time.sleep(1)

            # Останавливаем наблюдатель
            if self.observer:
                self.observer.stop()
                self.observer.join()

        except Exception as e:
            self.log_signal.emit(f"Ошибка: {str(e)}")
        finally:
            self.finished.emit()

    @pyqtSlot()
    def stop(self):
        self.is_running = False

    @pyqtSlot()
    def restore(self):
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

    def process_image(self, image_path):
        try:
            # Обрабатываем изображение
            processed_path = self.image_processor.process(image_path)

            if processed_path:
                # Добавляем в git
                self.git_manager.add_to_repo(processed_path)

        except Exception as e:
            self.log_signal.emit(f"Ошибка обработки {image_path}: {str(e)}")


class ImageEventHandler(FileSystemEventHandler):
    def __init__(self, worker):
        self.worker = worker

    def on_created(self, event):
        if not event.is_directory:
            image_exts = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp', '.heic')
            if event.src_path.lower().endswith(image_exts):
                self.worker.log_signal.emit(f"Обнаружено новое изображение: {event.src_path}")
                self.worker.process_image(event.src_path)