# QazTube

Простой клон YouTube на Django с загрузкой видео через Telegram бота.

## Установка

1. Создайте виртуальное окружение и активируйте его:
```bash
python -m venv venv
source venv/bin/activate  # для Linux/Mac
venv\Scripts\activate     # для Windows
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Примените миграции:
```bash
python manage.py migrate
```

4. Создайте суперпользователя:
```bash
python manage.py createsuperuser
```

5. Создайте бота в Telegram через @BotFather и получите токен

6. Отредактируйте `bot.py`, заменив `YOUR_BOT_TOKEN` на ваш токен

## Запуск

1. Запустите сервер Django:
```bash
python manage.py runserver
```

2. В отдельном терминале запустите бота:
```bash
python bot.py
```

3. Запустите сервер Gunicorn:
```bash
gunicorn -c gunicorn.conf.py main:app
```

## Использование

1. Отправьте боту видео с подписью в формате:
```
Название видео
Описание видео
```

2. Бот загрузит видео на сайт и отправит вам ссылку

3. Административная панель доступна по адресу: http://localhost:8000/admin/ 