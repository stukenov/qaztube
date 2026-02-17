import os
import logging
from django.conf import settings
from .models import Video
from datetime import timedelta
import cv2
import shutil
from .queue import VideoQueue
from PIL import Image
import io
import subprocess
import threading

# Get logger for this module
logger = logging.getLogger('videos')

def generate_thumbnail(video_path, output_path=None):
    """Generate thumbnail from video file"""
    try:
        # Open video file
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise Exception("Could not open video file")
            
        # Get video properties
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames == 0:
            raise Exception("Video has no frames")
            
        # Take frame from 10% of video
        frame_number = int(total_frames * 0.1)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        
        # Read frame
        ret, frame = cap.read()
        if not ret:
            raise Exception("Could not read frame")
            
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Convert to PIL Image
        image = Image.fromarray(frame_rgb)
        
        # Resize maintaining aspect ratio
        max_size = (640, 360)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Create thumbnails directory if it doesn't exist
        thumbnails_dir = os.path.join(settings.MEDIA_ROOT, 'thumbnails')
        os.makedirs(thumbnails_dir, exist_ok=True)
        
        # Generate output path if not provided
        if output_path is None:
            filename = os.path.splitext(os.path.basename(video_path))[0]
            output_path = os.path.join(thumbnails_dir, f"{filename}_thumb.jpg")
            
        # Save thumbnail
        image.save(output_path, 'JPEG', quality=85)
        
        # Clean up
        cap.release()
        
        # Return relative path from MEDIA_ROOT
        return os.path.relpath(output_path, settings.MEDIA_ROOT)
        
    except Exception as e:
        logger.error(f"Error generating thumbnail: {str(e)}")
        return None

def save_video(file_path, title, description="", additional_params=None):
    logger.info(f"Starting save_video function for {title}")
    
    # Создаем Video объект для получения uid
    video = Video.objects.create(
        title=title,
        description=description
    )
    
    # Создаем директорию видео
    video_dir = os.path.join(settings.MEDIA_ROOT, video.file_directory)
    os.makedirs(video_dir, exist_ok=True)
    
    # Копируем файл в структуру
    filename = f"video{os.path.splitext(file_path)[1]}"
    new_path = os.path.join(video_dir, filename)
    shutil.copy2(file_path, new_path)
    
    # Обновляем путь в модели
    video.video_file = os.path.relpath(new_path, settings.MEDIA_ROOT)
    
    # Получаем длительность
    cap = cv2.VideoCapture(new_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = timedelta(seconds=frame_count/fps)
    cap.release()
    
    video.duration = duration
    video.save()
    
    logger.info(f"Video saved with UID: {video.uid}")
    
    # Создаем задачу в очереди
    try:
        queue = VideoQueue()
        task_id = queue.create_task(
            input_path=new_path,
            output_path=os.path.join(video_dir, f"processed{os.path.splitext(filename)[1]}"),
            params={
                "video_id": video.id,
                "hls_path": os.path.join(video_dir, "master.m3u8"),
                "thumbnail_path": os.path.join(video_dir, "thumbnail.jpg"),
                "video_uid": video.uid
            }
        )
        video.transcoding_task_id = task_id
        video.save()
        logger.info(f"Created transcoding task {task_id}")
    except Exception as e:
        logger.error(f"Error creating transcoding task: {str(e)}")
        video.transcoding_status = 'failed'
        video.transcoding_error = f"Failed to create task: {str(e)}"
        video.save()
    
    return video
