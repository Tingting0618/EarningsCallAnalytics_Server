# Generated by Django 4.0.3 on 2022-03-06 03:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('earningscall_api', '0003_appuser'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='followers',
            field=models.ManyToManyField(related_name='following', to='earningscall_api.appuser'),
        ),
    ]
