from django.db import migrations, models
import videos.models

class Migration(migrations.Migration):
    dependencies = [
        ('videos', '0005_add_video_uid'),
    ]

    operations = [
        migrations.AddField(
            model_name='video',
            name='hls_file',
            field=models.FileField(blank=True, null=True, upload_to=videos.models.get_hls_path),
        ),
        # Обновляем функции upload_to для остальных полей
        migrations.AlterField(
            model_name='video',
            name='video_file',
            field=models.FileField(upload_to=videos.models.get_video_path),
        ),
        migrations.AlterField(
            model_name='video',
            name='processed_video',
            field=models.FileField(blank=True, null=True, upload_to=videos.models.get_processed_video_path),
        ),
        migrations.AlterField(
            model_name='video',
            name='thumbnail',
            field=models.ImageField(blank=True, upload_to=videos.models.get_thumbnail_path),
        ),
    ] 