# Generated by Django 2.2.7 on 2020-01-13 23:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0007_auto_20200113_2229'),
    ]

    operations = [
        migrations.AddField(
            model_name='system',
            name='build',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='build_systems', to='system.SystemBuild'),
        ),
        migrations.AddField(
            model_name='system',
            name='firmware',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='firmware_systems', to='system.HubFirmware'),
        ),
        migrations.AddField(
            model_name='tag',
            name='build',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='build_tags', to='system.TagBuild'),
        ),
    ]