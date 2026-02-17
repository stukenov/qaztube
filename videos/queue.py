import os
import json
import uuid
import time
import logging
from datetime import datetime
from django.conf import settings

logger = logging.getLogger('videos')

class VideoQueue:
    def __init__(self):
        self.base_dir = os.path.join(settings.MEDIA_ROOT, 'queue')
        self.dirs = {
            'pending': os.path.join(self.base_dir, 'pending'),
            'processing': os.path.join(self.base_dir, 'processing'),
            'done': os.path.join(self.base_dir, 'done'),
            'failed': os.path.join(self.base_dir, 'failed'),
            'delayed': os.path.join(self.base_dir, 'delayed'),
            'logs': os.path.join(self.base_dir, 'logs')
        }
        self._create_directories()
    
    def _create_directories(self):
        """Create all necessary queue directories"""
        for dir_path in self.dirs.values():
            os.makedirs(dir_path, exist_ok=True)
    
    def _generate_task_id(self):
        """Generate unique task ID"""
        return str(uuid.uuid4())
    
    def _get_task_path(self, task_id, state):
        """Get full path for task file in specified state"""
        return os.path.join(self.dirs[state], f"{task_id}.task")
    
    def _get_log_path(self, task_id):
        """Get full path for task log file"""
        return os.path.join(self.dirs['logs'], f"{task_id}.log")
    
    def create_task(self, input_path, output_path, params=None, max_retries=3):
        """Create new task and add it to pending queue"""
        task_id = self._generate_task_id()
        task_data = {
            "input": input_path,
            "output": output_path,
            "params": params or {},
            "retry": 0,
            "max_retries": max_retries,
            "created_at": datetime.now().isoformat()
        }
        
        task_path = self._get_task_path(task_id, 'pending')
        with open(task_path, 'w') as f:
            json.dump(task_data, f, indent=2)
        
        logger.info(f"Created new task {task_id} in pending queue")
        return task_id
    
    def grab_task(self):
        """Atomically grab next task from pending queue"""
        # Get all pending tasks sorted by creation time
        pending_tasks = []
        for filename in os.listdir(self.dirs['pending']):
            if filename.endswith('.task'):
                task_path = os.path.join(self.dirs['pending'], filename)
                pending_tasks.append((task_path, os.path.getctime(task_path)))
        
        if not pending_tasks:
            return None
        
        # Sort by creation time and get oldest task
        pending_tasks.sort(key=lambda x: x[1])
        task_path, _ = pending_tasks[0]
        
        # Try to move task to processing
        task_id = os.path.splitext(os.path.basename(task_path))[0]
        processing_path = self._get_task_path(task_id, 'processing')
        
        try:
            os.rename(task_path, processing_path)
            logger.info(f"Grabbed task {task_id} for processing")
            return task_id
        except OSError:
            logger.warning(f"Failed to grab task {task_id}, already taken")
            return None
    
    def complete_task(self, task_id, success=True):
        """Move task to done or failed state"""
        if success:
            source_dir = 'processing'
            target_dir = 'done'
            logger.info(f"Task {task_id} completed successfully")
        else:
            source_dir = 'processing'
            target_dir = 'failed'
            logger.info(f"Task {task_id} failed")
        
        source_path = self._get_task_path(task_id, source_dir)
        target_path = self._get_task_path(task_id, target_dir)
        
        try:
            os.rename(source_path, target_path)
        except OSError as e:
            logger.error(f"Failed to move task {task_id}: {str(e)}")
    
    def retry_failed_task(self, task_id):
        """Move failed task back to pending with increased retry count"""
        failed_path = self._get_task_path(task_id, 'failed')
        pending_path = self._get_task_path(task_id, 'pending')
        
        try:
            # Read task data
            with open(failed_path, 'r') as f:
                task_data = json.load(f)
            
            # Increase retry count
            task_data['retry'] += 1
            task_data['last_retry'] = datetime.now().isoformat()
            
            # Write updated data to pending
            with open(pending_path, 'w') as f:
                json.dump(task_data, f, indent=2)
            
            # Remove from failed
            os.remove(failed_path)
            
            logger.info(f"Retried task {task_id} (attempt {task_data['retry']})")
            return True
        except Exception as e:
            logger.error(f"Failed to retry task {task_id}: {str(e)}")
            return False
    
    def get_task_status(self, task_id):
        """Get current status of task"""
        for state, dir_path in self.dirs.items():
            if state == 'logs':
                continue
            task_path = self._get_task_path(task_id, state)
            if os.path.exists(task_path):
                return state
        return None
    
    def get_task_data(self, task_id):
        """Get task data from any state"""
        for state, dir_path in self.dirs.items():
            if state == 'logs':
                continue
            task_path = self._get_task_path(task_id, state)
            if os.path.exists(task_path):
                with open(task_path, 'r') as f:
                    return json.load(f)
        return None
    
    def get_task_log(self, task_id):
        """Get task log content"""
        log_path = self._get_log_path(task_id)
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                return f.read()
        return None
    
    def write_log(self, task_id, message):
        """Write message to task log"""
        log_path = self._get_log_path(task_id)
        with open(log_path, 'a') as f:
            timestamp = datetime.now().isoformat()
            f.write(f"[{timestamp}] {message}\n")
    
    def cleanup_old_tasks(self, days=7):
        """Remove old completed tasks and their logs"""
        now = time.time()
        for state in ['done', 'failed']:
            dir_path = self.dirs[state]
            for filename in os.listdir(dir_path):
                if filename.endswith('.task'):
                    file_path = os.path.join(dir_path, filename)
                    if now - os.path.getctime(file_path) > days * 86400:
                        task_id = os.path.splitext(filename)[0]
                        try:
                            os.remove(file_path)
                            log_path = self._get_log_path(task_id)
                            if os.path.exists(log_path):
                                os.remove(log_path)
                            logger.info(f"Cleaned up old task {task_id}")
                        except Exception as e:
                            logger.error(f"Failed to cleanup task {task_id}: {str(e)}") 