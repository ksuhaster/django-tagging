from django.db import models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tagging', '0001_initial'),
    ]

    operations = [
        migrations.AddField('Tag', 'en_name', models.CharField(
            verbose_name='uk name', max_length=50, blank=True,
            default='')),
        migrations.AddField('Tag', 'uk_name', models.CharField(
            verbose_name='uk name', max_length=50, blank=True,
            default='')),
    ]
