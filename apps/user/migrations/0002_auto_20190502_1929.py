# Generated by Django 2.2 on 2019-05-02 19:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='sync_id',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.AddField(
            model_name='userimage',
            name='sync_id',
            field=models.PositiveIntegerField(null=True),
        ),
    ]
