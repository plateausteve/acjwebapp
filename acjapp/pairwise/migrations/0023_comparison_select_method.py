# Generated by Django 3.1 on 2020-12-23 20:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pairwise', '0022_comparison_average_diff_est_act'),
    ]

    operations = [
        migrations.AddField(
            model_name='comparison',
            name='select_method',
            field=models.CharField(default='', max_length=30, verbose_name='method of selecting next comparison'),
        ),
    ]
