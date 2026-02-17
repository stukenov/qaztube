import unittest
import os
import tempfile
import shutil
from videos.queue import VideoQueue

class TestVideoQueue(unittest.TestCase):
    def setUp(self):
        # Создаем временную директорию для тестов
        self.test_dir = tempfile.mkdtemp()
        self.queue = VideoQueue()
        self.queue.base_dir = self.test_dir
        self.queue._create_directories()

    def tearDown(self):
        # Удаляем временную директорию после тестов
        shutil.rmtree(self.test_dir)

    def test_create_task(self):
        task_id = self.queue.create_task(
            input_path='test_input.mp4',
            output_path='test_output.mp4'
        )
        self.assertIsNotNone(task_id)
        task_path = self.queue._get_task_path(task_id, 'pending')
        self.assertTrue(os.path.exists(task_path))

    def test_get_task_status(self):
        task_id = self.queue.create_task(
            input_path='test_input.mp4',
            output_path='test_output.mp4'
        )
        status = self.queue.get_task_status(task_id)
        self.assertEqual(status, 'pending')

    def test_write_log(self):
        task_id = self.queue.create_task(
            input_path='test_input.mp4',
            output_path='test_output.mp4'
        )
        test_message = "Test log message"
        self.queue.write_log(task_id, test_message)
        log_content = self.queue.get_task_log(task_id)
        self.assertIn(test_message, log_content)

if __name__ == '__main__':
    unittest.main() 