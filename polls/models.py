from django.db import models

# Create your models here.

class NoVote(models.Model):
    constituency_id = models.IntegerField(default=0)
    created_date = models.DateTimeField('date created')

class Vote(NoVote):
    candidate_id = models.IntegerField(default=0)
    party_id = models.IntegerField(default=0)
