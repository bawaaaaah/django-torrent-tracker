from django.db import models
from tracker.models import Torrent

"""
class Tracker(models.Model):
    dwn	= models.positiveintegerfield() # total torrent downloads
    seeds = models.positiveintegerfield()
    leechers = models.positiveintegerfield()
    pr = models.ManyToManyField(Torrent) # 10 most downloaded
    active = models.ManyToManyField(Torrent) # 10 most active
    most_seeded = models.ManyToManyField(Torrent) # 10 most seeded torrents
    most_leeched = models.ManyToManyField(Torrent) # 10 most leeched torrents
    files = models.positiveintegerfield()
"""

class DailySearch(models.Model):
    phrase = models.TextField()

class Search(models.Model):
    phrase = models.TextField()
    cnt = models.PositiveIntegerField()

class Sections(models.Model):
   cat = models.CharField(max_length=50, unique=True)
   cnt = models.IntegerField(blank=True, null=True)

