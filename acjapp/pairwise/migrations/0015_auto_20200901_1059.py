# Generated by Django 3.1 on 2020-09-01 16:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pairwise', '0014_auto_20200901_1052'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comparison',
            name='count_same_p',
        ),
        migrations.AddField(
            model_name='script',
            name='count_same_p',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]