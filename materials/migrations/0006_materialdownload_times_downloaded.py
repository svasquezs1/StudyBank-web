from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('materials', '0005_materialdownload_materialrating'),
    ]

    operations = [
        migrations.AddField(
            model_name='materialdownload',
            name='times_downloaded',
            field=models.PositiveIntegerField(default=1),
        ),
    ]