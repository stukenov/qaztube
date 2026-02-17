import os
import subprocess
import time
import logging
import json
from django.conf import settings
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qaztube.settings')
django.setup()

from videos.models import Video
from videos.queue import VideoQueue
import cv2
from PIL import Image

logger = logging.getLogger('videos')

class VideoWorker:
    def __init__(self):
        self.queue = VideoQueue()
        self.running = False
    
    def start(self):
        """Запуск воркера"""
        self.running = True
        logger.info("Video worker started")
        
        while self.running:
            try:
                # Пытаемся взять задачу
                task_id = self.queue.grab_task()
                if task_id:
                    logger.debug(f"Task {task_id} grabbed for processing")
                    self._process_task(task_id)
                else:
                    # Нет задач, ждем
                    logger.debug("No tasks available, sleeping for 1 second")
                    time.sleep(1)
            except Exception as e:
                logger.error(f"Error in worker loop: {str(e)}")
                time.sleep(5)
    
    def stop(self):
        """Остановка воркера"""
        self.running = False
        logger.info("Video worker stopped")
    
    def _process_task(self, task_id):
        """Обработка одной задачи"""
        logger.info(f"Processing task {task_id}")
        
        try:
            # Получаем данные задачи
            task_data = self.queue.get_task_data(task_id)
            if not task_data:
                raise Exception("Task data not found")
            logger.debug(f"Task data for {task_id}: {task_data}")
            
            # Получаем видео из Django
            video_id = task_data['params']['video_id']
            video = Video.objects.get(id=video_id)
            logger.debug(f"Video object retrieved: {video}")
            
            # Проверяем входной файл
            input_path = task_data['input']
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"Input file not found: {input_path}")
            logger.debug(f"Input file exists: {input_path}")
            
            # Обновляем статус
            video.transcoding_status = 'processing'
            video.save()
            logger.debug(f"Video status updated to processing for {video_id}")
            
            # Транскодируем в H.264
            output_path = task_data['output']
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            logger.debug(f"Output directory created: {os.path.dirname(output_path)}")
            
            cmd_process = [
                'ffmpeg', '-i', input_path,
                '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
                '-c:a', 'aac', '-b:a', '128k',
                '-movflags', '+faststart',
                output_path
            ]
            
            logger.debug(f"Running FFmpeg command: {' '.join(cmd_process)}")
            process = subprocess.Popen(
                ' '.join(cmd_process),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                shell=True
            )
            
            stdout, stderr = process.communicate()
            logger.debug(f"FFmpeg stdout: {stdout}")
            logger.debug(f"FFmpeg stderr: {stderr}")
            
            if process.returncode != 0:
                raise Exception(f"FFmpeg processing failed: {stderr}")
            
            # Создаем HLS поток
            hls_path = task_data['params']['hls_path']
            os.makedirs(os.path.dirname(hls_path), exist_ok=True)
            logger.debug(f"HLS directory created: {os.path.dirname(hls_path)}")
            
            cmd_hls = [
                'ffmpeg', '-i', output_path,
                '-c:v', 'libx264', '-preset', 'medium',
                '-c:a', 'aac', '-b:a', '128k',
                '-f', 'hls',
                '-hls_time', '10',
                '-hls_list_size', '0',
                '-hls_segment_filename', 
                os.path.join(os.path.dirname(hls_path), "segment%03d.ts"),
                hls_path
            ]
            
            logger.debug(f"Running FFmpeg HLS command: {' '.join(cmd_hls)}")
            process = subprocess.Popen(
                ' '.join(cmd_hls),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                shell=True
            )
            
            stdout, stderr = process.communicate()
            logger.debug(f"FFmpeg HLS stdout: {stdout}")
            logger.debug(f"FFmpeg HLS stderr: {stderr}")
            
            if process.returncode != 0:
                raise Exception(f"FFmpeg HLS conversion failed: {stderr}")
            
            # Генерируем превью
            thumbnail_path = task_data['params']['thumbnail_path']
            cap = cv2.VideoCapture(output_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_number = int(total_frames * 0.1)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()
            cap.release()
            logger.debug(f"Thumbnail frame captured: {ret}")
            
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(frame_rgb)
                max_size = (640, 360)
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
                image.save(thumbnail_path, 'JPEG', quality=85)
                logger.debug(f"Thumbnail saved at: {thumbnail_path}")
            
            # Обновляем модель видео
            video.processed_video = os.path.relpath(output_path, settings.MEDIA_ROOT)
            video.hls_file = os.path.relpath(hls_path, settings.MEDIA_ROOT)
            video.thumbnail = os.path.relpath(thumbnail_path, settings.MEDIA_ROOT)
            video.transcoding_status = 'completed'
            video.transcoding_progress = 100
            video.save()
            logger.debug(f"Video model updated for {video_id}")
            
            # Завершаем задачу
            self.queue.complete_task(task_id, success=True)
            logger.info(f"Task {task_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Error processing task {task_id}: {str(e)}")
            self.queue.write_log(task_id, f"Error: {str(e)}")
            self.queue.complete_task(task_id, success=False)
            
            if 'video' in locals():
                video.transcoding_status = 'failed'
                video.transcoding_error = str(e)
                video.save()
                logger.debug(f"Video status updated to failed for {video_id}")
    
    def retry_failed_tasks(self):
        """Повторная попытка для неудачных задач"""
        failed_dir = self.queue.dirs['failed']
        logger.debug(f"Retrying failed tasks in directory: {failed_dir}")
        for filename in os.listdir(failed_dir):
            if filename.endswith('.task'):
                task_id = os.path.splitext(filename)[0]
                task_data = self.queue.get_task_data(task_id)
                if task_data and task_data['retry'] < task_data['max_retries']:
                    logger.debug(f"Retrying task {task_id}")
                    self.queue.retry_failed_task(task_id)
    
    def cleanup_old_tasks(self, days=7):
        """Очистка старых задач"""
        logger.debug(f"Cleaning up tasks older than {days} days")
        self.queue.cleanup_old_tasks(days) 

if __name__ == '__main__':
    worker = VideoWorker()
    worker.start()
