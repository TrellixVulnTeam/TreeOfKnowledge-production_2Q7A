# Generated by Django 2.0.8 on 2019-07-12 18:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('collection', '0067_simulation_model_is_timeseries_analysis'),
    ]

    operations = [
        migrations.CreateModel(
            name='Likelihood_fuction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rule_id', models.IntegerField()),
                ('simulation_id', models.IntegerField()),
                ('beta_distribution_a', models.FloatField()),
                ('beta_distribution_b', models.FloatField()),
            ],
        ),
    ]
