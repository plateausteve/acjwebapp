# Generated by Django 3.0.8 on 2020-08-01 18:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pairwise', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='script',
            old_name='of_set',
            new_name='set',
        ),
        migrations.RenameField(
            model_name='script',
            old_name='of_user',
            new_name='user',
        ),
        migrations.RenameField(
            model_name='set',
            old_name='of_user',
            new_name='user',
        ),
        migrations.AddField(
            model_name='script',
            name='image',
            field=models.FileField(blank=True, null=True, upload_to='scripts/images'),
        ),
        migrations.AddField(
            model_name='script',
            name='pdf',
            field=models.FileField(blank=True, null=True, upload_to='scripts/pdfs'),
        ),
    ]
