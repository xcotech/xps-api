# Generated by Django 2.2.7 on 2020-01-08 22:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracking', '0009_auto_20200108_2225'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='activityfav',
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name='activityfav',
            constraint=models.UniqueConstraint(fields=('user', 'activity'), name='unique_user_favs'),
        ),
    ]