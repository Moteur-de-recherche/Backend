# Generated by Django 5.1.6 on 2025-02-12 00:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('book', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='index',
            name='positions',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
