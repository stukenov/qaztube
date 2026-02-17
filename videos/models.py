import os
import string
import random
from django.db import models
from django.utils import timezone

def generate_uid():
    """Генерирует 6-символьный uid из букв в нижнем регистре и цифр"""
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(6))

def get_video_path(instance, filename):
    """Создает путь для файла видео на основе uid"""
    ext = os.path.splitext(filename)[1]
    if not instance.uid:
        instance.uid = generate_uid()
    path = '/'.join(instance.uid)  # Создает путь a/b/c/1/2/3
    return f'videos/{path}/video{ext}'

def get_processed_video_path(instance, filename):
    """Создает путь для обработанного видео на основе uid"""
    ext = os.path.splitext(filename)[1]
    if not instance.uid:
        instance.uid = generate_uid()
    path = '/'.join(instance.uid)
    return f'videos/{path}/processed{ext}'

def get_hls_path(instance, filename):
    """Создает путь для HLS файлов"""
    if not instance.uid:
        instance.uid = generate_uid()
    path = '/'.join(instance.uid)
    return f'videos/{path}/master.m3u8'

def get_thumbnail_path(instance, filename):
    """Создает путь для thumbnail на основе uid"""
    ext = os.path.splitext(filename)[1]
    if not instance.uid:
        instance.uid = generate_uid()
    path = '/'.join(instance.uid)
    return f'videos/{path}/thumbnail{ext}'

class Video(models.Model):
    TRANSCODING_STATUS = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    uid = models.CharField(max_length=6, unique=True, db_index=True, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    video_file = models.FileField(upload_to=get_video_path)
    processed_video = models.FileField(upload_to=get_processed_video_path, null=True, blank=True)
    hls_file = models.FileField(upload_to=get_hls_path, null=True, blank=True)
    thumbnail = models.ImageField(upload_to=get_thumbnail_path, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    views = models.PositiveIntegerField(default=0)
    duration = models.DurationField(null=True, blank=True)
    transcoding_status = models.CharField(max_length=20, choices=TRANSCODING_STATUS, default='pending')
    transcoding_error = models.TextField(null=True, blank=True)
    transcoding_progress = models.IntegerField(default=0)
    transcoding_task_id = models.CharField(max_length=36, null=True, blank=True)
    
    def __str__(self):
        return f"{self.title} ({self.uid})"
    
    def save(self, *args, **kwargs):
        if not self.uid:
            # Генерируем uid при создании
            while True:
                uid = generate_uid()
                if not Video.objects.filter(uid=uid).exists():
                    self.uid = uid
                    break
        super().save(*args, **kwargs)
    
    @property
    def file_directory(self):
        """Возвращает путь к директории файлов видео"""
        return f"videos/{'/'.join(self.uid)}"
    
    class Meta:
        ordering = ['-created_at']
