from django.db import models

# Create your models here.

class Vote(models.Model):
    constituency_id = models.IntegerField(default=0)
    #Candidate ID may be -1 or a valid PopitPerson ID.
    candidate_id = models.IntegerField(default=0)
    #Quick helper so we can calculate results.
    party_id = models.CharField(default=0, max_length=16)

    def __unicode__(self):
        return '%d: %d (%s)' % (self.constituency_id, self.candidate_id, self.party_id)
