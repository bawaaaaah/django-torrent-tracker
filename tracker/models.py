from django.db import models
from users.models import User
from fields import BigInt

User.add_to_class('passkey', models.CharField(max_length=40, null=True, blank=True))

class Torrent(models.Model):
    author = models.ForeignKey(User, blank=True)
    fn = models.CharField(max_length=255, db_index=True)
    info_hash = models.CharField(max_length=40)
    info = models.TextField()
    bytes = BigInt()
    dwn	= models.IntegerField(blank=True, null=True)
