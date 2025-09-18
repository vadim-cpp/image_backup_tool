import os
from PIL import Image


class ImageProcessor:
    def __init__(self, settings, log_signal):
        self.settings = settings
        self.log_signal = log_signal

    def process(self, image_path):
        try:
            with Image.open(image_path) as img:
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

                # Создаем имя файла
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                output_path = os.path.join(
                    os.path.dirname(image_path),
                    f"{base_name}_compressed.{self.settings['compression_format']}"
                )

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