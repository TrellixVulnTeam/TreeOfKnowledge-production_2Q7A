# Generated by Django 2.0.8 on 2020-06-01 10:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('collection', '0096_simulation_model_execution_order_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='simulation_model',
            name='not_used_rules',
            field=models.TextField(default='{}'),
            preserve_default=False,
        ),
    ]
