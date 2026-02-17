from django.db import migrations, models
import string
import random

def generate_uid():
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(6))

def init_video_uids(apps, schema_editor):
    Video = apps.get_model('videos', 'Video')
    for video in Video.objects.all():
        while True:
            uid = generate_uid()
            if not Video.objects.filter(uid=uid).exists():
                video.uid = uid
                video.save()
                break

class Migration(migrations.Migration):
    dependencies = [
        ('videos', '0004_video_transcoding_task_id'),
    ]

    operations = [
        # Сначала добавляем поле как nullable
        migrations.AddField(
            model_name='video',
            name='uid',
            field=models.CharField(max_length=6, null=True),
        ),
        # Генерируем uid для существующих записей
        migrations.RunPython(init_video_uids),
        # Делаем поле уникальным и обязательным
        migrations.AlterField(
            model_name='video',
            name='uid',
            field=models.CharField(max_length=6, unique=True, db_index=True, editable=False),
        ),
    ] 