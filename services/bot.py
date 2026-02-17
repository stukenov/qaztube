import os
import logging
from pathlib import Path
from telegram import Update, File
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qaztube.settings')
django.setup()
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from videos.upload import save_video
from asgiref.sync import sync_to_async
from typing import Optional, Union
from telegram.ext._application import Application as TelegramApplication
from videos.models import Video as VideoModel

logger: logging.Logger = logging.getLogger('bot')

class Bot:
    TOKEN: str = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    TEMP_DIR: Path = Path(__file__).parent / 'temp'

    def __init__(self) -> None:
        self.application: TelegramApplication = Application.builder().token(self.TOKEN).build()
        self.TEMP_DIR.mkdir(exist_ok=True)
        self.save_video_async = sync_to_async(save_video)
        self._setup_handlers()
        logger.info("Bot initialized")

    def _setup_handlers(self) -> None:
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(MessageHandler(filters.VIDEO, self.handle_video))
        logger.info("Handlers set up")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.info("Received start command")
        await update.message.reply_text(
            "Привет! Отправь мне видео, и я загружу его на сайт.\n"
            "Формат: отправь видео с подписью в формате:\n"
            "Название видео\n"
            "Описание видео"
        )

    async def handle_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.info("Handling video message")
        if not update.message.video:
            logger.warning("No video found in message")
            await update.message.reply_text("Пожалуйста, отправьте видео файл.")
            return

        video_file: File = await update.message.video.get_file()
        temp_file_path: Path = self.TEMP_DIR / f"video_{update.message.message_id}.mp4"
        logger.info(f"Downloading video to {temp_file_path}")

        try:
            await video_file.download_to_drive(temp_file_path)
            caption: str = update.message.caption or ""
            title: str = caption.split('\n')[0] if caption else "Без названия"
            description: str = '\n'.join(caption.split('\n')[1:]) if len(caption.split('\n')) > 1 else ""
            logger.info(f"Video title: {title}, description: {description}")
            video: VideoModel = await self.save_video_async(str(temp_file_path), title, description)

            await update.message.reply_text(
                f"Видео успешно загружено!\n"
                f"Название: {video.title}\n"
                f"ID: {video.uid}"
            )
            logger.info(f"Video uploaded successfully: {video.title} (ID: {video.uid})")

        except Exception as e:
            logger.error(f"Error uploading video: {str(e)}")
            await update.message.reply_text(f"Ошибка при загрузке видео: {str(e)}")

        finally:
            if temp_file_path.exists():
                temp_file_path.unlink()
                logger.info(f"Temporary file {temp_file_path} deleted")

    def start(self) -> None:
        logger.info("Starting bot polling")
        self.application.run_polling()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    bot: Bot = Bot()
    bot.start()