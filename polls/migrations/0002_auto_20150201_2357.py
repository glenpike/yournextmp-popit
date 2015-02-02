# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vote',
            name='party_id',
            field=models.CharField(default=0, max_length=16),
            preserve_default=True,
        ),
    ]
