# Generated by Django 3.1 on 2020-09-06 01:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pairwise', '0017_auto_20200903_2039'),
    ]

    operations = [
        migrations.RenameField(
            model_name='script',
            old_name='lo_hi95ci',
            new_name='hi95ci',
        ),
        migrations.RenameField(
            model_name='script',
            old_name='lo_lo95ci',
            new_name='lo95ci',
        ),
    ]
