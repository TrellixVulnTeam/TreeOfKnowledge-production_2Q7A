# Generated by Django 2.0.8 on 2019-05-13 08:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('collection', '0049_auto_20190508_1402'),
    ]

    operations = [
        migrations.AddField(
            model_name='attribute',
            name='object_type_of_related_object',
            field=models.TextField(null=True),
        ),
    ]
