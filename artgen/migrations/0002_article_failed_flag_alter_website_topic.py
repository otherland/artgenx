# Generated by Django 4.2.3 on 2023-07-27 13:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('artgen', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='failed_flag',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='website',
            name='topic',
            field=models.CharField(max_length=100, unique=True),
        ),
    ]