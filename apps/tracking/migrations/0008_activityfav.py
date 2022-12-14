# Generated by Django 2.2.7 on 2019-12-26 20:12

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tracking', '0007_auto_20190524_0337'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActivityFav',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('sync_id', models.PositiveIntegerField(null=True)),
                ('note', models.CharField(blank=True, max_length=255)),
                ('activity', models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='fav_users', to='tracking.Activity')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='favs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created'],
            },
        ),
    ]
