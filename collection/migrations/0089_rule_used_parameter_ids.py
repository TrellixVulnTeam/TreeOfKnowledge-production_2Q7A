# Generated by Django 2.0.8 on 2020-01-28 13:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('collection', '0088_auto_20200127_1753'),
    ]

    operations = [
        migrations.AddField(
            model_name='rule',
            name='used_parameter_ids',
            field=models.TextField(default='[]'),
            preserve_default=False,
        ),
    ]