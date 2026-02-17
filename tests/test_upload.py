import unittest
import os
import tempfile
from videos.upload import generate_thumbnail

class TestUploadFunctions(unittest.TestCase):
    def test_generate_thumbnail(self):
        # Создаем временный файл для тестового видео
        with tempfile.NamedTemporaryFile(suffix='.mp4') as temp_video:
            # Генерируем временный путь для thumbnail
            temp_thumb = tempfile.mktemp(suffix='.jpg')
            
            # Тест возвращает None для несуществующего видео
            result = generate_thumbnail('nonexistent.mp4')
            self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main() 