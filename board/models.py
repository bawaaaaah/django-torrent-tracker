from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import pre_delete

from utils import genslug, slughifi
import board.managers
import re
import os
import datetime

class Forum(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=255)
    group = models.CharField(max_length=255, blank=True)
    ordering = models.IntegerField(default=0)

    objects = board.managers.ForumManager()

    def save(self):
	self.slug=slughifi(self.name)
	if not re.sub('\s+-', '', self.slug) or len(self.slug) > 50:
	    self.slug = genslug()
	self.slug = self.slug.replace(' ', '-')
	try:
	    super(Forum, self).save()
	except:
	    self.slug = genslug()
	    super(Forum, self).save()

    class Meta:
	ordering = ['ordering', 'group']

    class Admin:
	list_display = ['name', 'ordering', 'group']

    def __unicode__(self):
	return self.name

class Moderator(models.Model):
    forum = models.ForeignKey(Forum)
    user = models.ForeignKey(User)

class Thread(models.Model):
    subject = models.CharField(max_length=160)
    forum = models.ForeignKey(Forum)
    closed = models.BooleanField(default=False)
    # Category sticky - will show up at the top of category listings.
    csticky = models.BooleanField(default=False)
    # Global sticky - will show up at the top of home listing.
    gsticky = models.BooleanField(default=False)
    slug = models.SlugField(unique=True)

    objects = models.Manager()
    view_manager = board.managers.ThreadManager()

    def __unicode__(self):
	return self.subject

    def get_url(self):
	return '/threads/%s/' % self.slug
    
    def save(self):
	self.slug=slughifi(self.subject)
	if not re.sub('\s+-', '', self.slug) or len(self.slug) > 50:
	    self.slug = genslug()
	self.slug = self.slug.replace(' ', '-')
	try:
	    super(Thread, self).save()
	except:
	    self.slug = genslug()
	    super(Thread, self).save()
	return self.slug

    class Admin:
	list_display = ('subject', 'forum')
	list_filter = ('closed', 'csticky', 'gsticky', 'forum')

class Post(models.Model):
    author = models.ForeignKey(User, editable=False, blank=True, default=None)
    thread = models.ForeignKey(Thread)
    text = models.TextField()
    changed = models.DateTimeField(editable=False, auto_now_add=True)
    ip = models.IPAddressField(blank=True)
    created = models.DateTimeField(editable=False, null=True)
    censored = models.BooleanField(default=False)
    freespeech = models.BooleanField(default=True)
    image = models.CharField(max_length=255, blank=True, null=True)

    objects = models.Manager()
    view_manager = board.managers.PostManager()

    def save(self, request):
	self.ip = request.META.get('REMOTE_ADDR', '127.0.0.7')
	if not self.id:
	    self.created = datetime.datetime.now()
	super(Post, self).save()

    def get_absolute_url(self):
	return '/threads/%s/#%s'%(self.thread.slug, self.id)

    def get_edit_form(self):
	from board.forms import PostForm
	return PostForm(initial={'text':self.text})

    def __unicode__(self):
	return '%s : %s' % (self.author, self.created)

    class Admin:
	list_display = ('author', 'created', 'thread', 'ip')


class AbuseReport(models.Model):
    """
    When an abuse report is filed by a registered User, the post is listed
    in this table.
    
    If the abuse report is rejected as false, the post.freespeech flag can be
    set to disallow further abuse reports on said thread.
    """
    post = models.ForeignKey(Post)
    submitter = models.ForeignKey(User)

    class Admin:
	list_display = ('post', 'submitter')

    class Meta:
	unique_together = (('post', 'submitter'),)

class BannedIP(models.Model):
    """
    The objects in this model are not allowed to log in or register new
    accounts.
    """
    iplist = models.IPAddressField()
    reason = models.TextField()

    def get_ips(self):
	return [i.strip() for i in str(self.iplist).splitlines()]

    def __unicode__(self):
	return ','.join(self.get_ips())

    class Admin:
	pass

def _drop_pics(sender, instance, signal, *args, **kwargs):
    from settings import MEDIA_ROOT
    try:
	os.unlink(os.path.join(MEDIA_ROOT, 'poster', instance.image))
	os.unlink(os.path.join(MEDIA_ROOT, 'iposter', instance.image))
    except OSError:
	pass

pre_delete.connect(_drop_pics, sender=Post)
