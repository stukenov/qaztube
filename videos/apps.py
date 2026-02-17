from django.apps import AppConfig
import threading
import asyncio


class VideosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'videos'

    # def ready(self):
        # # Избегаем двойного запуска в режиме разработки
        # import os
        # if os.environ.get('RUN_MAIN'):
        #     # Запуск воркера
        #     from ..qaztube.services.worker import VideoWorker
        #     worker = VideoWorker()
        #     worker_thread = threading.Thread(target=worker.start)
        #     worker_thread.daemon = True
        #     worker_thread.start()

        #     # Запуск бота
        #     from .bot import application
        #     def run_bot():
        #         loop = asyncio.new_event_loop()
        #         asyncio.set_event_loop(loop)
        #         loop.run_until_complete(application.run_polling())
            
        #     bot_thread = threading.Thread(target=run_bot)
        #     bot_thread.daemon = True
        #     bot_thread.start()
