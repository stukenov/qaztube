import unittest
import os
import tempfile
import shutil
from services.worker import VideoWorker

class TestVideoWorker(unittest.TestCase):
    def setUp(self):
        self.worker = VideoWorker()
        self.test_dir = tempfile.mkdtemp()
        self.worker.queue.base_dir = self.test_dir
        self.worker.queue._create_directories()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_retry_failed_tasks(self):
        # Создаем тестовую задачу
        task_id = self.worker.queue.create_task(
            input_path='test_input.mp4',
            output_path='test_output.mp4',
            max_retries=3
        )
        
        # Перемещаем задачу в failed
        failed_path = self.worker.queue._get_task_path(task_id, 'failed')
        pending_path = self.worker.queue._get_task_path(task_id, 'pending')
        os.rename(pending_path, failed_path)
        
        # Проверяем retry_failed_tasks
        self.worker.retry_failed_tasks()
        
        # Задача должна вернуться в pending
        self.assertEqual(self.worker.queue.get_task_status(task_id), 'pending')

    def test_cleanup_old_tasks(self):
        # Создаем тестовую задачу
        task_id = self.worker.queue.create_task(
            input_path='test_input.mp4',
            output_path='test_output.mp4'
        )
        
        # Перемещаем в done
        done_path = self.worker.queue._get_task_path(task_id, 'done')
        pending_path = self.worker.queue._get_task_path(task_id, 'pending')
        os.rename(pending_path, done_path)
        
        # Тестируем очистку с 0 дней (немедленно)
        self.worker.cleanup_old_tasks(days=0)
        
        # Проверяем что задача удалена
        self.assertIsNone(self.worker.queue.get_task_status(task_id))

if __name__ == '__main__':
    unittest.main() 