# Generated by Django 3.1 on 2020-09-01 03:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pairwise', '0012_auto_20200830_0904'),
    ]

    operations = [
        migrations.AddField(
            model_name='comparison',
            name='form_start_variable',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='comparison',
            name='difficulty_rating',
            field=models.IntegerField(choices=[(0, 'Not At All Difficult'), (1, 'Not Too Difficult'), (2, 'Difficult'), (3, 'Very Difficult')], default=0, verbose_name='how difficult is the comparison to judge?'),
        ),
        migrations.AlterField(
            model_name='comparison',
            name='interest_rating',
            field=models.IntegerField(choices=[(1, 'Not At All Interesting'), (2, 'Not Interesting'), (3, 'Neutral'), (4, 'Interesting'), (5, 'Very Interesting')], default=3, verbose_name='how interesting is this comparison'),
        ),
        migrations.AlterField(
            model_name='comparison',
            name='uninterrupted',
            field=models.IntegerField(choices=[(1, 'Uninterrupted'), (0, 'Interrupted')], default=1, verbose_name='is the comparison interrupted or uninterrupted allowing valid duration computation'),
        ),
    ]
