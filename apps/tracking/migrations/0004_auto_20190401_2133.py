# Generated by Django 2.1.7 on 2019-04-01 21:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tracking', '0003_activitydata_sensors'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='session',
            options={'ordering': ['-created']},
        ),
    ]
