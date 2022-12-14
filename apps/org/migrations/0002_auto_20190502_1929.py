# Generated by Django 2.2 on 2019-05-02 19:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('org', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='org',
            name='sync_id',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.AddField(
            model_name='orgmember',
            name='sync_id',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.AddField(
            model_name='orgsystem',
            name='sync_id',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.AddField(
            model_name='orgtag',
            name='sync_id',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.AddField(
            model_name='team',
            name='sync_id',
            field=models.PositiveIntegerField(null=True),
        ),
    ]
