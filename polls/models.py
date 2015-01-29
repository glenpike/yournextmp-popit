from django.db import models

# Create your models here.

class Vote(models.Model):
    constituency_id = models.IntegerField(default=0)
    #Candidate ID may be -1 or a valid PopitPerson ID.
    candidate_id = models.IntegerField(default=0)
    #Quick helper so we can calculate results.
    party_id = models.IntegerField(default=0)
