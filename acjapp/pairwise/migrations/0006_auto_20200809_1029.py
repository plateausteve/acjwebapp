# Generated by Django 3.1 on 2020-08-09 16:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pairwise', '0005_comparison_set'),
    ]

    operations = [
        migrations.AlterField(
            model_name='set',
            name='cor_est_to_actual',
            field=models.FloatField(default=0),
        ),
    ]
