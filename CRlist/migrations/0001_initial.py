# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-09-10 16:08
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('courseid', models.CharField(max_length=30)),
                ('title', models.CharField(max_length=100)),
                ('cate', models.CharField(max_length=30)),
                ('overview', models.CharField(max_length=300)),
            ],
        ),
        migrations.CreateModel(
            name='Course_list',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('clist', models.CharField(max_length=300)),
                ('course', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='CRlist.Course')),
            ],
        ),
    ]
