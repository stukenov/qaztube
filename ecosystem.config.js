module.exports = {
  apps: [
    {
      name: 'qaztube-web',
      script: '.venv/bin/gunicorn',
      args: 'qaztube.wsgi:application --bind 127.0.0.1:8000 --workers 3',
      interpreter: 'none',
      cwd: '/srv/www/live.31kz.adapto.kz/qaztube',
      env: {
        DJANGO_SETTINGS_MODULE: 'qaztube.settings',
        PYTHONPATH: '/srv/www/live.31kz.adapto.kz/qaztube'
      }
    },
    {
      name: 'qaztube-bot',
      script: 'services/bot.py',
      interpreter: '.venv/bin/python',
      cwd: '/srv/www/live.31kz.adapto.kz/qaztube',
      env: {
        DJANGO_SETTINGS_MODULE: 'qaztube.settings',
        PYTHONPATH: '/srv/www/live.31kz.adapto.kz/qaztube'
      }
    },
    {
      name: 'qaztube-worker',
      script: 'services/worker.py',
      interpreter: '.venv/bin/python',
      cwd: '/srv/www/live.31kz.adapto.kz/qaztube',
      env: {
        DJANGO_SETTINGS_MODULE: 'qaztube.settings',
        PYTHONPATH: '/srv/www/live.31kz.adapto.kz/qaztube'
      }
    }
  ]
}