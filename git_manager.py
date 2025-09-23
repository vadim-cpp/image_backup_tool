import os
import shutil
from git import Repo, GitCommandError


class GitManager:
    def __init__(self, settings, log_signal):
        self.settings = settings
        self.log_signal = log_signal
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.repo_path = os.path.join(current_dir, "backup_repo")
        self.repo = None

    def init_repo(self):
        try:
            # Клонируем или открываем репозиторий
            if not os.path.exists(self.repo_path):
                os.makedirs(self.repo_path, exist_ok=True)
                self.log_signal.emit(f"Клонирование репозитория в {self.repo_path}")
                self.repo = Repo.clone_from(self.settings['repo_url'], self.repo_path)
            else:
                self.log_signal.emit("Открытие существующего репозитория")
                self.repo = Repo(self.repo_path)
                # Pull последних изменений
                origin = self.repo.remote('origin')
                origin.pull()

            return True
        except GitCommandError as e:
            self.log_signal.emit(f"Ошибка Git: {str(e)}")
            return False

    def add_to_repo(self, file_path):
        try:
            # Копируем файл в репозиторий
            repo_file_path = os.path.join(self.repo_path, os.path.basename(file_path))
            shutil.copy2(file_path, repo_file_path)

            # Добавляем и коммитим
            self.repo.index.add([os.path.basename(file_path)])
            self.repo.index.commit(f"Add {os.path.basename(file_path)}")

            # Пушим изменения
            origin = self.repo.remote('origin')
            origin.push()

            self.log_signal.emit(f"Файл {os.path.basename(file_path)} добавлен в репозиторий")

        except GitCommandError as e:
            self.log_signal.emit(f"Ошибка Git при добавлении файла: {str(e)}")

    def add_multiple_to_repo(self, file_paths):
        """Добавляет несколько файлов одним коммитом"""
        try:
            added_files = []

            for file_path in file_paths:
                # Копируем файл в репозиторий
                repo_file_path = os.path.join(self.repo_path, os.path.basename(file_path))
                shutil.copy2(file_path, repo_file_path)
                added_files.append(os.path.basename(file_path))

            # Добавляем все файлы одним коммитом
            self.repo.index.add(added_files)
            self.repo.index.commit(f"Add {len(added_files)} images")

            # Пушим изменения
            origin = self.repo.remote('origin')
            origin.push()

            self.log_signal.emit(f"Добавлено файлов в репозиторий: {len(added_files)}")

        except GitCommandError as e:
            self.log_signal.emit(f"Ошибка Git при добавлении файлов: {str(e)}")

    def restore_repo(self):
        try:
            restore_path = os.path.join(os.path.expanduser("~"), "restored_images")

            if not os.path.exists(restore_path):
                os.makedirs(restore_path)

            # Клонируем репозиторий
            if os.path.exists(self.repo_path):
                shutil.rmtree(self.repo_path)

            self.log_signal.emit("Клонирование репозитория для восстановления...")
            repo = Repo.clone_from(self.settings['repo_url'], self.repo_path)

            # Копируем файлы
            for item in os.listdir(self.repo_path):
                if item != '.git':
                    src_path = os.path.join(self.repo_path, item)
                    dst_path = os.path.join(restore_path, item)

                    if os.path.isdir(src_path):
                        shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                    else:
                        shutil.copy2(src_path, dst_path)

            self.log_signal.emit(f"Изображения восстановлены в: {restore_path}")
            return True

        except Exception as e:
            self.log_signal.emit(f"Ошибка восстановления: {str(e)}")
            return False

    def process(self, image_path):
        try:
            with Image.open(image_path) as img:
                # Конвертируем в RGB если нужно (для JPEG)
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')

                # Изменяем размер если нужно
                if self.settings['resize_enabled']:
                    img.thumbnail((self.settings['max_size'], self.settings['max_size']), Image.Resampling.LANCZOS)

                # Определяем формат сохранения
                format_map = {
                    'webp': 'WEBP',
                    'jpeg': 'JPEG',
                    'avif': 'AVIF'
                }
                save_format = format_map.get(self.settings['compression_format'], 'WEBP')

                # Создаем имя файла (сохраняем оригинальное имя)
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                output_filename = f"{base_name}_compressed.{self.settings['compression_format']}"
                output_path = os.path.join(self.processed_dir, output_filename)

                # Сохраняем с нужным качеством
                save_params = {
                    'quality': self.settings['compression_quality'],
                    'optimize': True
                }

                # Особые параметры для WebP
                if save_format == 'WEBP':
                    save_params['method'] = 6  # Максимальное сжатие

                img.save(output_path, save_format, **save_params)

                self.log_signal.emit(f"Изображение обработано: {output_path}")
                return output_path

        except Exception as e:
            self.log_signal.emit(f"Ошибка обработки изображения {image_path}: {str(e)}")
            return None