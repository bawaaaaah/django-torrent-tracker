from django.db import models
from fs.models import Topic
from users.models import User
from fields import Dict
from django.utils.translation import ugettext_lazy as _

STATUS = (
    ('pending', _('pending')),
    ('progress', _('in progress')),
    ('suspended', _('suspended')),
    ('stuck', _('stuck')),
    ('notfound', _('file not found')),
    ('done', _('finished')),
)
 
class Queue(models.Model):
    def __init__(self, *args, **kwargs):
	super(Queue, self).__init__(*args, **kwargs)
	self.attrs = Dict(self)
    topic = models.ForeignKey(Topic, blank=True, null=True)
    user = models.ForeignKey(User, blank=True, related_name='transcoding_queue')
    submit_date = models.DateTimeField(auto_now_add=True)
    order = models.CharField(blank=True, null=True, max_length=10)
    status = models.CharField(null=True,blank=True, max_length=250, choices=STATUS)
    file = models.TextField(null=True, blank=True)
    prefs = models.TextField(null=True, blank=True)

class TorrentGenQueue(models.Model):
    topic = models.ForeignKey(Topic, blank=True, related_name='torrentq')
    submit_date = models.DateTimeField(auto_now_add=True)

class FS(models.Model):
    username = models.CharField(max_length=255)
    path = models.TextField()
    ls = models.TextField()

