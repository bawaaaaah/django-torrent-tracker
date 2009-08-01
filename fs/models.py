# -*- coding:utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.db.models.signals import pre_delete
from cPickle import dumps, loads, UnpicklingError
import re
import os
from tagging.models import Tag
from tracker.models import Torrent
from fields import Dict
from utils import slughifi, genslug
import settings

def drop_pics(instance):
    scrs = instance.attrs.get('scrs')
    if scrs:
	for fn in scrs:
	    try:
		os.unlink(os.path.join(settings.MEDIA_ROOT, 'scr', fn))
		os.unlink(os.path.join(settings.MEDIA_ROOT, 'iscr', fn))
	    except OSError:
		pass
    try:
	os.unlink(os.path.join(settings.MEDIA_ROOT, 'poster', instance.poster))
	os.unlink(os.path.join(settings.MEDIA_ROOT, 'iposter', instance.poster))
    except OSError:
	pass

def _drop_pics(sender, instance, signal, *args, **kwargs):
    drop_pics(instance)
    if instance.attrs.has_key('videos'):
	for fn in instance.attrs['videos']:
	    try:
		os.unlink(os.path.join(settings.MEDIA_ROOT, 'flvs', fn))
	    except OSError:
		raise
		#pass

def _update_user_attrs(sender, instance, signal, *args, **kwargs):
    if instance.author.attrs.has_key('votes'):
	if instance.author.attrs['votes'].has_key(instance.id):
	    del instance.author.attrs['votes'][instance.id]
	    instance.author.save()

# SECTIONS should be list of unique items

SECTIONS = (
    ('misc', _("misc")),
    ('anime', _("anime")),
    ('books', _("books")),
    ('games', _("games")),
    ('movies', _("movies")),
    ('music', _("music")),
    ('pics', _("pictures")),
    ('tv', _("tv")),
)

AKINDS = (
    ('anime_unk', _("unknown")),
    ('martial', _("martial arts")),
    ('vampires', _("vampires")),
    ('war', _("war")),
    ('detective', _("detective")),
    ('anime_drama', _("drama")),
    ('history', _("history")),
    ('cyberpunk', _("cyberpank")),
    ('anime_comedy', _("comedy")),
    ('mahou', _("mahou shoujo")),
    ('mecha', _("mecha")),
    ('anime_mystery', _("mystery")),
    ('anime_musical', _("musical")),
    ('parody', _("parody")),
    ('routine', _("routine")),
    ('police', _("police")),
    ('postapocalyptic', _("postapocalyptic")),
    ('anime_adventure', _("adventure")),
    ('psychology', _("psychology")),
    ('romanticism', _("romanticism")),
    ('samurai', _("samurais")),
    ('shoujo', _("shoujo")),
    ('shounen', _("shounen")),
    ('shounen-ai', _("shounen-ai")),
    ('fairy-tale', _("fairy tale")),
    ('anime_sport', _("sport")),
    ('anime_thriller', _("thriller")),
    ('school', _("school")),
    ('sci-fi', _("sci-fi")),
    ('anime_fantasy', _("fantasy")),
    ('erotic', _("erotic")),
    ('anime_horror', _("horror")),
    ('hentai', _("hentai")),
    ('yuri', _("yuri")),
    ('yaoi', _("yaoi")),
)

BKINDS = (
    ('ebook', _('ebooks')),
    ('audio', _('audio books')),
)

GKINDS = (
    ('game_unk', _("unknown")),
    ('dreamcast', _("dreamcast")),
    ('fixes', _("game fixes/patches")),
    ('cube', _("GameCube")),
    ('linux', _("Linux")),
    ('mac', _("Mac")),
    ('mobile', _("mobile phones")),
    ('nintendo', _("Nintendo DS")),
    ('palm', _("Palm, PocketPC & IPAQ")),
    ('ps2', _("PS2")),
    ('psx', _("PSX")),
    ('psp', _("PSP")),
    ('retro', _("ROMS / retro")),
    ('sega', _("Sega Saturn")),
    ('demo', _("video demonstrations")),
    ('wii', _("Wii")),
    ('windows', _("Windows")),
    ('kinds', _("Windows - Kids Games")),
    ('xbox', _("XBox")),
    ('360', _("XBox 360")),
)

MKINDS = (
    ('mov_other', _("other")),
    ('action', _("action")),
    ('adventure', _("adventure")),
    ('animation', _("animation")),
    ('asian', _("asian")),
    ('ahorror', _("asian horror")),
    ('clip', _("clip")),
    ('comedy', _("comedy")),
    ('concert', _("concerts")),
    ('disney', _("disney")),
    ('doc', _("documentary")),
    ('drama', _("drama")),
    ('family', _("family")),
    ('fantasy', _("fantasy")),
    ('horror', _("horror")),
    ('kids', _("kids")),
    ('musical', _("musicals")),
    ('mystery', _("mystery")),
    ('trailer', _("trailers")),
    ('sc-fi', _("sci-fi")),
    ('sport', _("sports related")),
    ('thriller', _("thriller")),
    ('western', _("westerns")),
)

OKINDS = (
    ('ongaku_unk', _("unknown")),
    ('alt',_("alternative")),
    ('ost',_("OST")),
    ('ongaku_asian',_("asian")),
    ('blues',_("blues")),
    ('book', _("book")),
    ('christ',_("christian")),
    ('poprock',_("classic Pop/Rock")),
    ('classical',_("classical")),
    ('country',_("country / western")),
    ('drum',_("drum-n-bass")),
    ('electro',_("electronic")),
    ('game',_("game Music")),
    ('goth',_("gothic")),
    ('hard',_("hardcore")),
    ('radio',_("hardHouse/old school radio mixes")),
    ('heavy',_("heavy/death metal")),
    ('metal',_("metal")),
    ('hip',_("hip hop")),
    ('industrial',_("industrial")),
    ('jazz',_("jazz")),
    ('karaoke',_("karaoke")),
    ('pop',_("pop")),
    ('punk',_("punk")),
    ('rnb',_("R&B")),
    ('rap',_("rap")),
    ('regge',_("reggae")),
    ('rock',_("rock")),
    ('ska',_("ska")),
    ('track',_("soundtracks")),
    ('spanish',_("spanish")),
    ('techno',_("techno")),
    ('trance',_("trance / house / dance")),
    ('unsigned',_("unsigned/Amateur")),
    ('ongaku_clip',_("video clips")),
)

PKINDS = (
    ('pic_unk', _("unknown")),
    ('pic_other',_("other")),
    ('scr',_("screenSavers")),
    ('wallp',_("wallpapers")),
    ('manga', _("manga")),
    ('hentai-manga', _("hentai manga")),
)

TKINDS = (
    ('tv_other', _("other")),
    ('show', _("tv Show")),
    ('serial', _("tv serial")),
)

def get_cat(name):
    # get category name by its subcategory name
    if name in [i[0] for i in AKINDS]:
	return 'anime'
    elif name in [i[0] for i in BKINDS]:
	return 'books'
    elif name in [i[0] for i in GKINDS]:
	return 'games'
    elif name in [i[0] for i in MKINDS]:
	return 'movies'
    elif name in [i[0] for i in OKINDS]:
	return 'music'
    elif name in [i[0] for i in PKINDS]:
	return 'pics'
    elif name in [i[0] for i in TKINDS]:
	return 'tv'
    else:
	for i in SECTIONS:
	    if i[0] == name:
		return i[1]

class Topic(models.Model):
    def __init__(self, *args, **kwargs):
	super(Topic, self).__init__(*args, **kwargs)
	self.attrs = Dict(self)
    author = models.ForeignKey(User)
    title = models.CharField(max_length=255, verbose_name=_("title"))
    slug = models.SlugField(db_index=True, blank=True, null=True, unique=True)
    text = models.TextField()
    poster = models.CharField(max_length=255, verbose_name=_("poster"))
    approved = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    prefs = models.TextField(null=True, blank=True)
    torrent = models.ForeignKey(Torrent, blank=True, null=True)

    section = models.CharField(max_length=50, choices=SECTIONS, default='misc', db_index=True)
    subcat = models.CharField(max_length=50, choices=AKINDS+BKINDS+GKINDS+MKINDS+OKINDS+PKINDS+TKINDS, default='misc', db_index=True)

    def add_rate(self, value):
	if value == 0: return
	if self.author.attrs.has_key('votes'):
	    votes = self.author.attrs.get('votes', {})
	    if not votes.has_key(self.id):
		votes.update({self.id: value})
	    else:
		return
	    self.author.attrs['votes'] = votes
	else:
	    self.author.attrs['votes'] = {self.id: value}
	self.author.save()
	if self.attrs.has_key('votes'):
	    self.attrs['votes'] += 1
	else:
	    self.attrs['votes'] = 1
	if self.attrs.has_key('ratings'):
	    self.attrs['ratings'].append(value)
	else:
	    self.attrs['ratings'] = [value]
	self.attrs['avg'] = sum(self.attrs['ratings'])/len(self.attrs['ratings'])
	self.save()

    def get_average(self):
	return '%.1f' % self.rate_average

    def html(self):
	from django.utils.safestring import mark_safe
	from django.utils.html import linebreaks, escape
	result = linebreaks(escape(self.text))
	result = re.sub(ur'\B--\B', u'—', result)
	return mark_safe(result)
    
    def save(self):
	self.slug = slughifi(self.title)
	if not re.sub('\s+-', '', self.slug) or len(self.slug) > 50:
	    self.slug = genslug()
	self.slug = self.slug.replace(' ', '-')
	self.author.attrs['posts'] = Topic.objects.filter(author=self.author).count()
	self.author.save()
	try:
	    super(Topic, self).save()
	except:
	    self.slug = genslug()
	    super(Topic, self).save()

    def _get_tags(self):
	return Tag.objects.get_for_object(self)
    def _set_tags(self, tag_list):
	Tag.objects.update_tags(self, tag_list)
    tags = property(_get_tags, _set_tags)

    def get_absolute_url(self):
	return "/~%s/%s/"%(self.author.username, self.slug)

    def __unicode__(self):
	return self.title

class Comment(models.Model):
    topic = models.ForeignKey(Topic, related_name='comment')
    created = models.DateTimeField(auto_now_add=True)
    image = models.CharField(blank=True, null=True, max_length=255)
    parent = models.ForeignKey('self', blank=True, null=True, related_name='child')
    prefs =  models.TextField(blank=True, null=True)
    """
  #this will be in pickle
  #moder_comment = models.TextField(blank=True, null=True, help_text=_("Moderator's comments."))
  #is_featured  = models.BooleanField(_("Display on the user first page"), default=False)
  #notify = models.BooleanField(_("Send notifications to author when comment added"), default=False)
  #capacity = models.DecimalField(_("The sum of sizes of related files"), null=True, blank=True, max_digits=19, decimal_places=0)
  #genre = models.OneToOneField(Genre, null=True, blank=True)
  """

    class Meta:
	ordering = ['-id']

    class Admin:
	pass

class Subscription(models.Model):
    user = models.ForeignKey(User, unique=True, related_name="subs_tags")
    beats = models.ManyToManyField(User, blank=True, null=True)

    def _get_tags(self):
	return Tag.objects.get_for_object(self)

    def _set_tags(self, tag_list):
	Tag.objects.update_tags(self, tag_list)
    tags = property(_get_tags, _set_tags)


class Message(models.Model):
    _SUBS_TYPES = (
	('tag', 'tag'),
	('user', 'user')
    )
    subscription = models.ForeignKey(Subscription, related_name="msg")
    type = models.CharField(max_length=5, choices=_SUBS_TYPES)

pre_delete.connect(_drop_pics, sender=Topic)
pre_delete.connect(_update_user_attrs, sender=Topic)

