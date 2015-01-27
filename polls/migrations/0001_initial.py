# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='NoVote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('constituency_id', models.IntegerField(default=0)),
                ('created_date', models.DateTimeField(verbose_name=b'date created')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('novote_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='polls.NoVote')),
                ('candidate_id', models.IntegerField(default=0)),
                ('party_id', models.IntegerField(default=0)),
            ],
            options={
            },
            bases=('polls.novote',),
        ),
    ]
