# Generated by Django 2.0.8 on 2019-05-15 08:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('collection', '0052_auto_20190515_1057'),
    ]

    operations = [
        migrations.AlterField(
            model_name='data_point',
            name='valid_time_end',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='data_point',
            name='valid_time_start',
            field=models.IntegerField(null=True),
        ),
    ]
