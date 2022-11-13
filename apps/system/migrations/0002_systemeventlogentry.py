# Generated by Django 2.2 on 2019-04-25 19:38

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SystemEventLogEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('log_entry', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('system', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='log_entries', to='system.System')),
            ],
            options={
                'ordering': ['-created'],
            },
        ),
    ]