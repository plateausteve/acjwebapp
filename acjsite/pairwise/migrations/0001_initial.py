# Generated by Django 3.0.8 on 2020-08-01 16:27

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Set',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('published_date', models.DateTimeField(blank=True, null=True)),
                ('of_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='the user who uploaded the scripts of this set')),
            ],
        ),
        migrations.CreateModel(
            name='Script',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('parameter_value', models.PositiveSmallIntegerField(verbose_name='the hidden parameter value to be compared by the user in development')),
                ('wins_in_set', models.PositiveSmallIntegerField(default=0, verbose_name='count of all comparisons in which this script wins')),
                ('comps_in_set', models.PositiveSmallIntegerField(default=0, verbose_name='count of all comparisons with this script')),
                ('prob_of_win_in_set', models.FloatField(default=0, verbose_name='ratio of wins to comparisons for this script')),
                ('lo_of_win_in_set', models.FloatField(default=0, verbose_name='log odds of winning for this script')),
                ('estimated_parameter_in_set', models.FloatField(default=0, verbose_name='estimated parameter from comparisons of this script')),
                ('rsme_in_set', models.FloatField(default=0, verbose_name='RSME of parameter for this script')),
                ('of_set', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='pairwise.Set', verbose_name='the one set to which the script belongs')),
                ('of_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='the user who uploaded the script')),
            ],
        ),
        migrations.CreateModel(
            name='Comparison',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('wini', models.PositiveSmallIntegerField(choices=[(0, 'Lesser'), (1, 'Greater')], verbose_name='is left script lesser or greater?')),
                ('winj', models.PositiveSmallIntegerField(choices=[(0, 'Lesser'), (1, 'Greater')], verbose_name='is right script lesser or greater?')),
                ('judge', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='the user judging the pair')),
                ('scripti', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='pairwise.Script', verbose_name='the left script in the comparison')),
                ('scriptj', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='pairwise.Script', verbose_name='the right script in the comparison')),
            ],
        ),
    ]