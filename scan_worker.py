import os
import time
import traceback
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot


class ScanWorker(QObject):
    log_signal = pyqtSignal(str)
    files_found = pyqtSignal(list)
    finished = pyqtSignal()

    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.files_to_commit = []

    def set_files_to_commit(self, file_list):
        """Устанавливает список файлов для фиксации"""
        self.files_to_commit = file_list

    @pyqtSlot()
    def scan(self):
        """Сканирует папку и возвращает список новых изображений"""
        try:
            self.log_signal.emit("Начало сканирования папки...")

            # Сканируем папку на наличие изображений
            found_files = self.scan_folder_for_images()

            # Отправляем найденные файлы через сигнал
            self.files_found.emit(found_files)
            self.log_signal.emit(f"Сканирование завершено. Найдено изображений: {len(found_files)}")

        except Exception as e:
            self.log_signal.emit(f"Ошибка при сканировании: {str(e)}")
            self.log_signal.emit(traceback.format_exc())
        finally:
            self.finished.emit()

    def scan_folder_for_images(self):
        """Рекурсивно сканирует папку и возвращает список изображений"""
        try:
            image_exts = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp', '.heic')
            found_files = []

            watch_folder = self.settings['watch_folder']

            if not os.path.exists(watch_folder):
                self.log_signal.emit(f"Ошибка: Папка {watch_folder} не существует")
                return []

            for root, dirs, files in os.walk(watch_folder):
                for file in files:
                    if file.lower().endswith(image_exts):
                        image_path = os.path.join(root, file)
                        # Исключаем уже обработанные файлы
                        if '_compressed.' not in file:
                            found_files.append(image_path)

            return found_files
        except Exception as e:
            self.log_signal.emit(f"Ошибка при сканировании папки: {str(e)}")
            return []

    @pyqtSlot()
    def commit_files(self):
        """Обрабатывает и фиксирует выбранные файлы в репозитории"""
        try:
            # Импортируем здесь, чтобы избежать проблем с многопоточностью
            from git_manager import GitManager
            from image_processor import ImageProcessor

            if not self.files_to_commit:
                self.log_signal.emit("Нет файлов для фиксации")
                self.finished.emit()
                return

            self.log_signal.emit("Инициализация репозитория...")

            # Инициализируем репозиторий
            git_manager = GitManager(self.settings, self.log_signal)
            if not git_manager.init_repo():
                self.log_signal.emit("Ошибка инициализации репозитория")
                self.finished.emit()
                return

            image_processor = ImageProcessor(self.settings, self.log_signal)
            processed_files = []

            # Обрабатываем каждый выбранный файл
            for i, file_path in enumerate(self.files_to_commit):
                self.log_signal.emit(
                    f"Обработка файла {i + 1}/{len(self.files_to_commit)}: {os.path.basename(file_path)}")
                processed_path = image_processor.process(file_path)
                if processed_path:
                    processed_files.append(processed_path)

            if processed_files:
                # Добавляем все файлы одним коммитом
                git_manager.add_multiple_to_repo(processed_files)
                self.log_signal.emit(f"Успешно зафиксировано файлов: {len(processed_files)}")

                # Очищаем временные файлы после успешной фиксации
                for processed_file in processed_files:
                    try:
                        if os.path.exists(processed_file):
                            os.remove(processed_file)
                    except Exception as e:
                        self.log_signal.emit(f"Ошибка при удалении временного файла: {str(e)}")
            else:
                self.log_signal.emit("Нет файлов для фиксации")

        except Exception as e:
            self.log_signal.emit(f"Ошибка при фиксации файлов: {str(e)}")
            self.log_signal.emit(traceback.format_exc())
        finally:
            self.finished.emit()

    @pyqtSlot()
    def restore(self):
        """Восстанавливает изображения из репозитория"""
        try:
            from git_manager import GitManager

            self.log_signal.emit("Начало восстановления...")
            git_manager = GitManager(self.settings, self.log_signal)
            if git_manager.restore_repo():
                self.log_signal.emit("Восстановление завершено успешно")
            else:
                self.log_signal.emit("Ошибка восстановления")
        except Exception as e:
            self.log_signal.emit(f"Ошибка при восстановлении: {str(e)}")
            self.log_signal.emit(traceback.format_exc())
        finally:
            self.finished.emit()