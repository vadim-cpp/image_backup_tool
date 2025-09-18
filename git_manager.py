import os
import shutil
from git import Repo, GitCommandError


class GitManager:
    def __init__(self, settings, log_signal):
        self.settings = settings
        self.log_signal = log_signal
        self.repo_path = os.path.join(os.path.expanduser("~"), ".image_backup_repo")
        self.repo = None
        print("self.settings: ", settings)
        print("self.repo_path: ", self.repo_path)

    def init_repo(self):
        try:
            # Клонируем или открываем репозиторий
            if not os.path.exists(self.repo_path):
                os.makedirs(self.repo_path)
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