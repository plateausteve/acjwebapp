# Generated by Django 3.1 on 2020-08-29 18:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pairwise', '0010_script_se'),
    ]

    operations = [
        migrations.AddField(
            model_name='script',
            name='stdev',
            field=models.FloatField(default=0, verbose_name='standard deviation of comps sample for this script'),
        ),
    ]