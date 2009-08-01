from django import forms
from django.utils.translation import ugettext_lazy as _
from fs.models import *
from tracker.models import Torrent
from utils import validate_image, save_imgs, mkstemp, sanitize_tags
from tagging.forms import TagField
from benc import bdecode, bencode
from settings import ANNOUNCE_URL, SITE_NAME, CENSORSHIP
import sha

class Select(forms.Select):
    # get rid of <select>
    def render(self, name, value, attrs=None, choices=()):
	from django.forms.util import flatatt
	from django.utils.encoding import force_unicode
	from itertools import chain
	from django.utils.html import escape, conditional_escape
	from django.utils.safestring import mark_safe
	if value is None: value = ''
	output = []
	# Normalize to string.
	str_value = force_unicode(value)
	for option_value, option_label in chain(self.choices, choices):
	    option_value = force_unicode(option_value)
	    selected_html = (option_value == str_value) and u' selected="selected"' or ''
	    output.append(u'<option value="%s"%s>%s</option>' % (
		escape(option_value), selected_html,
		conditional_escape(force_unicode(option_label))))
	return mark_safe(u''.join(output))

def _update_notification_delivery_queue(tags, user):
    from tagging.models import TaggedItem
    subs = TaggedItem.objects.get_by_model(Subscription, tags)
    s_ids = []
    for item in subs:
	if item.user.id != user.id:
	    m = item.msg.create()
	    m.type = 'tag'
	    m.save()
	    s_ids.append(item.id)
    subs = Subscription.objects.filter(beats=user)
    for item in subs:
	if item.id not in s_ids and item.id != user.id:
	    m = item.msg.create()
	    m.type='user'
	    m.save()

def _clean_torrent(hsh):
    import magic
    if hsh is None:
	return ''
    m = magic.open(magic.MAGIC_MIME)
    m.load()
    hsh = hsh.read()
    if not 'x-bittorrent' in m.buffer(hsh):
	m.close()
	raise forms.ValidationError, _("Uploaded file doesn't look like torrent.")
    m.close()
    try:
	# do not forget to add LimitRequestBody to apache config
	hsh = bdecode(hsh)
    except ValueError:
	raise forms.ValidationError, _("Uploaded file doesn't look like torrent.")
    hsh['announce'] = ANNOUNCE_URL
    hsh['modified-by'] = [SITE_NAME]
    if hsh.has_key('comment'):
	hsh['comment'] = SITE_NAME
    info_hash=sha.new(bencode(hsh['info'])).hexdigest()
    t = Torrent.objects.filter(info_hash=info_hash)
    if t:
	raise forms.ValidationError, _("This torrent already exists.")
    return (hsh, info_hash)

def _save_torrent(instance, data):
    from utils import slughifi, genslug
    import base64
    if not data:
	return
    slug = slughifi(instance.title)
    if not slug.strip().replace('-', '') or len(slug)>=50:
	slug = genslug()
    slug = slug.replace(' ', '-')
    fn = "%sxDF-%s.torrent"%(instance.author.id, slug)
    torrent = Torrent()
    torrent.fn = fn
    torrent.author = instance.author
    torrent.info_hash = data[1]
    if data[0]['info'].has_key('length'):
	file_length = data[0]['info']['length']
    else:
	file_length = reduce(lambda x,y: x+y, [f['length'] for f in data[0]['info']['files']])
    torrent.bytes = file_length
    hsh = base64.b64encode(bencode(data[0]))
    torrent.info = hsh
    torrent.save()
    instance.torrent = torrent

class TopicForm(forms.ModelForm):
    class Meta:
	model = Topic
	fields = ('title', 'tags', 'text', 'poster', 'torrent')
    title = forms.CharField(label=_("title"), max_length=255, widget=forms.TextInput)
    tags = forms.CharField(label=_("tags"), max_length=255, required=False, widget=forms.TextInput)

    text = forms.CharField(widget=forms.Textarea)
    poster = forms.ImageField(label=_("poster"))
    torrent = forms.FileField(required=True, label=_('.torrent file'))

    def clean_tags(self):
	return sanitize_tags(self.cleaned_data['tags'])

    def clean_title(self):
	title = unicode(self.cleaned_data['title'].strip())
	if len(title) == 0:
	    raise forms.ValidationError(_("title is required"))
	if title in [u'beats', u'posts'] or title.startswith(u'page-') or title.startswith(u'~'):
	    raise forms.ValidationError(_("you need to change title"))
	t = Topic.objects.filter(title=title, author=self.instance.author)
	if t:
	    raise forms.ValidationError(_("Post with this title already exists."))
	return title

    def clean_poster(self):
	return validate_image(self.cleaned_data['poster']) 

    def clean_torrent(self):
	return _clean_torrent(self.cleaned_data['torrent'])

    def clean_text(self):
	text = unicode(self.cleaned_data['text'].strip())
	if len(text) == 0:
	    raise forms.ValidationError("This field is required.")
	return text

    def save(self):
	from tagging.models import TaggedItem
	self.instance.poster = save_imgs(self.cleaned_data['poster'], self.instance.author.id, 'poster')
	self.instance.title=self.cleaned_data['title']
	self.instance.text=self.cleaned_data['text']
	if not CENSORSHIP:
	    self.instance.approved = True
	_save_torrent(self.instance, self.cleaned_data['torrent'])

	self.instance.save()
	self.instance.tags = self.cleaned_data['tags']
	_update_notification_delivery_queue(self.cleaned_data['tags'], self.instance.author)
	return self.instance.id

_YESNO = (
    ('yes', _('Yes')),
    ('no', _('No')),
)

class TopicEditForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
	super(TopicEditForm, self).__init__(*args, **kwargs)
	self.curcat = self.instance.section

    class Meta:
	model = Topic
	exclude = ('author', 'slug', 'rate_average', 'rate_count', 'vcount', 'rating', 'approved', 'prefs', 'created', 'torrent', 'subcat')

    def clean_title(self):
	title = unicode(self.cleaned_data['title'].strip())
	if len(title) == 0:
	    raise forms.ValidationError(_("title is required"))
	if title in [u'beats', u'posts'] or title.startswith(u'page-') or title.startswith(u'~'):
	   raise forms.ValidationError(_("you need to change title"))
	return title

    def clean_poster(self):
	return validate_image(self.cleaned_data['poster'])

    def clean_section(self):
	self.curcat = self.cleaned_data['section']
	return self.cleaned_data['section']

    def clean_tags(self):
	return sanitize_tags(self.cleaned_data['tags'])

    def clean_text(self):
	text = unicode(self.cleaned_data['text'].strip())
	if len(text) == 0:
	    raise forms.ValidationError("This field is required.")
	return text

    def clean_torrent(self):
	return _clean_torrent(self.cleaned_data['torrent'])

    def clean_year(self):
	if not self.cleaned_data['year']: return ''
	error_message = _("four-digit year expected")
	import time
	try:
	    y = self.cleaned_data['year']
	    return int(time.strptime(y, '%Y')[0])
	except ValueError:
	    raise forms.ValidationError(error_message)

    def save(self):
	torm = {'anime': ['imdb', 'artist', 'album', 'company'],
	    'books': ['artist', 'album', 'year', 'company', 'tube', 'imdb', 'scrs'],
	    'games': ['imdb', 'artist', 'album'],
	    'movies': ['artist', 'album', 'company'],
	    'music': ['scrs', 'imdb', 'company', 'tube', 'lngs'],
	    'pics': ['imdb', 'artist', 'album', 'year', 'company', 'tube'],
	    'tv': ['artist', 'album', 'company'],
	    'misc': ['scrs', 'imdb', 'artist', 'album', 'year', 'company', 'tube', 'lngs']
	}
	toadd = {'anime': ['year', 'tube', 'lngs'],
	    'books': ['lngs'],
	    'games': ['year', 'company', 'lngs', 'tube'],
	    'movies': ['imdb', 'year', 'tube', 'lngs'],
	    'music': ['album', 'artist', 'year'],
	    'pics': ['lngs'],
	    'tv': ['imdb', 'year', 'tube', 'lngs'],
	    'misc': [],
	}
	for k in torm.get(self.cleaned_data['section'], []):
	    del self.instance.attrs[k]
	for k in toadd.get(self.cleaned_data['section'], []):
	    self.instance.attrs[k] = self.cleaned_data[k]

	self.instance.section = self.cleaned_data['section']
	if self.cleaned_data['section'] == 'misc':
	    self.instance.subcat = 'misc'
	else:
	    self.instance.subcat = self.cleaned_data[self.cleaned_data['section']]

	if self.cleaned_data['notify'] == 'yes':
	    if self.instance.author.attrs.has_key('notify'):
		l = self.instance.author.attrs['notify']
		l.append(self.instance.id)
		self.instance.author.attrs['notify'] = l
	    else:
		self.instance.author.attrs['notify'] = [self.instance.id]
	if self.cleaned_data['featured'] == 'yes':
	    if self.instance.author.attrs.has_key('featured'):
		l = self.instance.author.attrs['featured']
		l.append(self.instance.id)
		self.instance.author.attrs['featured'] = l
	    else:
		self.instance.author.attrs['featured'] = [self.instance.id]
	if self.cleaned_data['poster']:
	    #removing old image if new uploaded
	    drop_pics(self.instance)
	if self.cleaned_data['poster']:
	    self.instance.poster = save_imgs(self.cleaned_data['poster'], self.instance.author.id, 'poster')
	self.instance.title = self.cleaned_data['title']
	self.instance.text = self.cleaned_data['text']
	_save_torrent(self.instance, self.cleaned_data['torrent'])

	if self.cleaned_data['tube']:
	    self.instance.attrs['tube'] = self.cleaned_data['tube']
	_update_notification_delivery_queue(self.cleaned_data['tags'], self.instance.author)
	self.instance.save()
	self.instance.tags = self.cleaned_data['tags']

    title = forms.CharField(max_length=255, widget=forms.TextInput, label=_("title"))
    tags = forms.CharField(max_length=255, required=False, widget=forms.TextInput, label=_("tags"))
    text = forms.CharField(widget=forms.Textarea)
 
    poster = forms.ImageField(required=False, label=_("poster"))
    torrent = forms.FileField(required=False, label=_('.torrent file'))

    section = forms.ChoiceField(required=False, label=_('category'), choices=SECTIONS, widget=Select)
    anime = forms.ChoiceField(required=False, choices=AKINDS, widget=Select)
    books = forms.ChoiceField(required=False, choices=BKINDS, widget=Select)
    games = forms.ChoiceField(required=False, choices=GKINDS, widget=Select)
    movies = forms.ChoiceField(required=False, choices=MKINDS, widget=Select)
    music = forms.ChoiceField(required=False, choices=OKINDS, widget=Select)
    pics = forms.ChoiceField(required=False, choices=PKINDS, widget=Select)
    tv = forms.ChoiceField(required=False, choices=TKINDS, widget=Select)

    imdb = forms.URLField(required=False, widget=forms.TextInput, label='IMDB URL')
    artist = forms.CharField(max_length=250, required=False, widget=forms.TextInput, label=_('artist'))
    album = forms.CharField(max_length=250, required=False, widget=forms.TextInput, label=_('album'))
    year = forms.CharField(required=False, max_length=4, label=_('year'), widget=forms.TextInput)
    company = forms.CharField(max_length=250, required=False, widget=forms.TextInput, label=_('company'))
    tube = forms.URLField(required=False, label=_('URL on external video'), widget=forms.TextInput)
    lngs = forms.CharField(max_length=100, required=False, label=_('languages'), widget=forms.TextInput)

    featured = forms.ChoiceField(required=False, label=_('featured'), widget=forms.RadioSelect, choices=_YESNO)
    notify = forms.ChoiceField(required=False, widget=forms.RadioSelect, label=_('notify on comments'), choices=_YESNO)

class ScreenshotForm(forms.Form):
    def __init__(self, topic, data=None, *args, **kwargs):
	super(ScreenshotForm, self).__init__(data, *args, **kwargs)
	self.topic = topic

    scr = forms.FileField()

    def clean_scr(self):
	return validate_image(self.cleaned_data['scr'])

    def save(self):
	l = self.topic.attrs.get('scrs', [])
	fn = save_imgs(self.cleaned_data['scr'], self.topic.author.id, 'scr')
	l.append(fn)
	self.topic.attrs['scrs'] = l
	self.topic.save()
