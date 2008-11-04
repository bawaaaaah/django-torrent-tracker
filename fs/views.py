from django.http import Http404, HttpResponseForbidden, HttpResponse, HttpResponseBadRequest
from django.db.models import Q
from django.core.cache import cache
from django.shortcuts import render_to_response, get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_http_methods
from django.template import RequestContext
from django.core.paginator import QuerySetPaginator, Paginator, InvalidPage

from tracker.models import Torrent
from fs.models import *
from fs.forms import *
from fs.util import sort_result
from users.forms import AuthForm
from users.views import login_required
from utils import HttpResponseRedirect, get_page
from settings import FTP_HOMEDIR, RESULTS_ON_PAGE, RECAPTCHA_PUB_KEY, RECAPTCHA_PRIVATE_KEY, MEDIA_ROOT, DATABASE_NAME, DATABASE_USER, DATABASE_PASSWORD, NUMBER_OF_POSTS_PER_DAY, MEMCACHE, ORPHANS, OPEN_TRACKER

@require_http_methods('GET')
def topic(request, username, slug=''):
    user = get_object_or_404(User, username=username)
    if not slug:
	last10 = Topic.objects.filter(author=user).order_by('-created')[:10]
	subs = user.attrs.get('beats')
	if subs:
	    subs = Topic.objects.filter(author__pk__in=subs).order_by('-created')[:10]
	return render_to_response('homepage.html', {
	    'last10': last10,
	    'subs': subs,
	    'object': user,
	}, context_instance=RequestContext(request))
    if slug not in ['posts', 'beats']:
	topic = get_object_or_404(Topic, slug=slug, author=user)
	return render_to_response('topic.html', {
	    'post': topic,
	}, context_instance=RequestContext(request))

    if slug == 'posts':
	q = QuerySetPaginator(
	    Topic.objects.filter(author=user).order_by('-created'),
	    RESULTS_ON_PAGE, orphans=5,
	)
	title = u"%s %s"%(_("All torrents of"), user.username)
    else: #beats
	q = user.attrs.get('beats', [])
	if q:
	    q = QuerySetPaginator(
		Topic.objects.filter(author__pk__in=result).order_by('-created'),
		RESULTS_ON_PAGE, orphans=5,
	    )
	else:
	    q = Paginator([], 1)
	title = u"%s %s"%(_("Subscription of"), user.username)

    q = get_page(request.GET.get('page', 0), q)

    return render_to_response('homepage.html', {
	'result': q,
    	'object': user,
	'title': title,
    }, context_instance=RequestContext(request))

def _sort_by(o, q):
    import cmemcache as memcache
    mc = memcache.Client([MEMCACHE], debug=0)
    peers = mc.get('peers')
    if not peers:
	peers = []
    if o == 'd':
	# date
	return q.order_by('-created')
    elif o == 'L':
	# Leechers Desc
	ids = [t['torrent__id'] for t in q.order_by('created').values('torrent__id')]
	return sort_result(ids, peers, by_seeds=False)
    elif o == 'l':
	# Leechers Asc
	ids = [t['torrent__id'] for t in q.order_by('-created').values('torrent__id')]
	return sort_result(ids, peers, asc=True, by_seeds=False)
    elif o == 'S':
	# Seeds Desc
	ids = [t['torrent__id'] for t in q.order_by('created').values('torrent__id')]
	return sort_result(ids, peers)
    elif o == 's':
	# Seeds Asc
	ids = [t['torrent__id'] for t in q.order_by('-created').values('torrent__id')]
	return sort_result(ids, peers, asc=True)
    elif o == 'B':
	# Size Desc
	return q.order_by('torrent__bytes')
    elif o == 'b':
	# Size Asc
	return q.order_by('-torrent__bytes')
    else:
	# date
	return result.order_by('-created')

@require_http_methods('GET')
def topic_list(request, slug=None):
    q = Topic.objects.filter(Q(section=slug)|Q(subcat=slug), approved=True)
    order = request.GET.get('order')
    args = ""
    if order in ['d', 'L', 'l', 'S', 's', 'B', 'b']:
	q = _sort_by(order, q)
	args = "?order=%s"%order
    q = get_page(request.GET.get('page', 0),
	QuerySetPaginator(q, RESULTS_ON_PAGE, orphans=ORPHANS),
    )

    return render_to_response('sections.html', {
	'result': q,
	'slug': slug,
	'args': args,
	'order': order,
    }, context_instance=RequestContext(request))

@login_required
def edit(request, the_id):
    topic = get_object_or_404(Topic, pk=the_id)
    if not request.user == topic.author:
	return HttpResponseForbidden('Permission denied')
    if topic.approved:
	return HttpResponseForbidden('This post approved by moderator and you cannot change it.')
    if request.method == 'POST':
	form = TopicEditForm(request.POST, request.FILES, instance=topic)
	if form.is_valid():
	    form.save()
	    return HttpResponseRedirect('/~%s/%s/'%(topic.author.username, topic.slug))
	return render_to_response('edit.html', {
	    'form': form,
	    'post': topic,
	}, context_instance=RequestContext(request))
    form = TopicEditForm(instance=topic)
    return render_to_response('edit.html', {
	'form': form,
	'post': topic,
    })

@login_required
def new(request):
    if request.method == 'GET':
	if not request.user.is_staff and request.user.attrs.has_key('posts_today'):
	    if request.user.attrs['posts_today'] >= NUMBER_OF_POSTS_PER_DAY:
		return render_to_response('add.html', {
		    'message': _("You can write only %s posts per day" % NUMBER_OF_POSTS_PER_DAY),
	    }, context_instance=RequestContext(request))
	form = TopicForm()
	return render_to_response('add.html', {
	    'form': form,
	}, context_instance=RequestContext(request))
    form = TopicForm(request.POST, request.FILES)
    form.instance.author = request.user
    if form.is_valid():
	inst_id = form.save()
	return HttpResponseRedirect('/edit/%s/'%inst_id)
    else:
	return render_to_response('add.html', {
	    'form': form,
	}, context_instance=RequestContext(request))

def _fail(msg=''):
    r = HttpResponse(mimetype="text/xml")
    r.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>")
    if msg:
	r.write("<list><msg>%s</msg></list>"%msg)
    else:
	r.write("<list><msg>failure</msg></list>")
    return r

@require_http_methods('GET')
def xml_tags(request, section, page=0):
    from tagging.models import Tag
    tag_list = Tag.objects.usage_for_model(Topic, filters=dict(section=section), counts=True)
    if not tag_list:
	return _fail()
    result = Paginator(tag_list, 30, 10)
    if not page and result.num_pages >0:
	page = result.num_pages
    try:
	r = result.page(int(page))
    except InvalidPage, ValueError:
	return _fail()
    return render_to_response('tags.xml', {
	'result': r,
	'page': page,
    }, mimetype = "text/xml")

@require_http_methods('POST')
def comment(request):
    from django.contrib.comments.views.comments import post_comment
    import captcha
    #captcha_html = captcha.displayhtml(settings.RECAPTCHA_PUB_KEY)
    msg = _("Captcha was incorrect")
    if request.POST.has_key('recaptcha_challenge_field') and request.POST.has_key('recaptcha_response_field'):
	captcha_response = captcha.submit(request.POST['recaptcha_challenge_field'], request.POST['recaptcha_response_field'], settings.RECAPTCHA_PRIVATE_KEY, request.META['REMOTE_ADDR'])
	if captcha_response.is_valid:
	    return post_comment(request, request.POST['target'])
    return HttpResponseBadRequest("cannot recognize this form")

@require_http_methods('POST')
def rate(request):
    def fallback():
	return render_to_response('rating.xml', {
	    'votes': 0,
	    'rating': 0,
	}, mimetype = "text/xml")
    try:
	post, rate = request.POST['post'], request.POST['rating']
    except KeyError:
	return fallback()
    try:
	post = int(post)
	rate = int(rate)
    except ValueError:
	return fallback()
    post = Topic.objects.filter(pk=post)
    if not post: return fallback()
    post = post[0]
    post.add_rate(rate)
    votes = 0
    if post.attrs.has_key('votes'):
	votes = post.attrs['votes']
    avg = 0
    if post.attrs.has_key('avg'):
	avg = post.attrs['avg']
    return render_to_response('rating.xml', {
	    'votes': votes,
	    'avg': avg,
	}, mimetype = "text/xml")

@require_http_methods('GET')
def search(request):
    import re
    from pysolr import Solr
    from stats.models import DailySearch
    from settings import SOLR_URL
    def _fail(query):
	# phrase is not changed, query is normalized phrase
	return render_to_response('search_results.html', {
	    'result': [],
	    'query': query,
	    'phrase': query,
	}, context_instance=RequestContext(request))
    phrase = request.GET.get('phrase')
    try:
	conn = Solr(SOLR_URL)
    except:
	return _fail(phrase)
    result = []
    if not phrase:
	raise Http404("Malformed request.")
    q = phrase
    if phrase.startswith('*') or phrase.startswith('?'):
	q = phrase[1:]
    q = q.strip()
    q = re.sub('['+'\[<>@\]'+']', '', q)
    q = re.sub('`', '"', q)
    q = re.sub('\s*:',':', q)
    q = re.sub('(?<!author)(?<!title)(?<!text)(?<!file)(?<!tag)(?<!artist)(?<!album)(?<!year)(?<!company)(?<!created):', ' ', q)
    if not q:
	return _fail(phrase)
    results = conn.search(q)
    if not results:
	return _fail(q)
    ids = [i['id'] for i in results]
    result = QuerySetPaginator(Topic.objects.filter(pk__in=ids), RESULTS_ON_PAGE, orphans=5)
    if result.num_pages == 0:
	return _fail(q)
    p = DailySearch.objects.create(phrase=q.strip())
    page = request.GET.get('page', 1)
    try:
	page = int(page)
	r = result.page(page)
    except (InvalidPage, ValueError):
	raise Http404("No such page")
    return render_to_response('search_results.html', {
	'result': r,
	'query': q,
	'phrase': phrase,
	'page': int(page),
	'title': phrase,
    }, context_instance=RequestContext(request))

def get_torrent(request, the_id):
    from users.views import login
    import base64
    from benc import bdecode, bencode
    if not OPEN_TRACKER:
	if not request.user.is_authenticated():
	    return HttpResponseRedirect(reverse(login) + '?redirect=' + request.path)
    torrent = get_object_or_404(Torrent, pk=the_id)
    content = base64.b64decode(torrent.info)
    content = bdecode(content)
    if not OPEN_TRACKER:
	content['announce'] += "?passkey=%s"%request.user.passkey
    content = bencode(content)
    response = HttpResponse(content, mimetype='application/x-bittorrent')
    response["Content-Length"] = len(content)
    response["Content-Disposition"] = "attachment; filename=\"%s\""% torrent.fn
    return response

@login_required
@require_http_methods('GET')
def subscribtion(request):
    from django.contrib.auth.models import User
    from django.core.exceptions import ValidationError
    r = HttpResponse(mimetype="text/xml")
    r.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>")
    if request.GET.has_key('uid'):
	try:
	    uid = int(request.GET['uid'])
	except ValueError:
	    if request.GET.has_key('xhr'):
		return _fail()
    	    raise Http404("No such user")
	user = User.objects.filter(pk=uid)
	if not user:
	    if request.GET.has_key('xhr'):
		return _fail()
    	    raise Http404("No such user")
	user = user[0]
	if user.id == request.user.id:
	    if request.GET.has_key('xhr'):
		return _fail()
    	    raise Http404("You cannot subscribe to yourself")
	if request.user.attrs.has_key('beats'):
	    if uid in request.user.attrs['beats']:
		a = request.user.attrs['beats']
		a.remove(uid)
		request.user.attrs['beats'] = a
	    else:
		a = request.user.attrs['beats']
		a.append(uid)
		request.user.attrs['beats'] = a
	else:
	    request.user.attrs['beats'] = [uid]
	request.user.save()

	if user.attrs.has_key('subscribers'):
	    if request.user.id in user.attrs['subscribers']:
		a = user.attrs['subscribers']
		a.remove(request.user.id)
		user.attrs['subscribers'] = a
	    else:
		a = user.attrs['subscribers']
		a.append(request.user.id)
		user.attrs['subscribers'] = a
	else:
	    user.attrs['subscribers'] = [request.user.id]
	user.save()

	subs = Subscription.objects.filter(user=request.user)
	if subs:
	    if user in subs[0].beats.all():
		subs[0].beats.remove(user)
	else:
	    subs = Subscription(user=request.user)
	    subs.save()
	    subs.beats.add(user)
	r.write("<result><msg>success</msg></result>")
	return r
    elif request.POST.has_key('tags'):
	from tagging.validators import isTagList
	from tagging.models import TaggedItem
	try:
	    isTagList(request.POST['tags'], {})
	except ValidationError:
	    if request.POST.has_key('xhr'):
		return _fail()
	    return HttpResponseForbidden("Seems you've supplied tags in improper format")
	item = Subscription.objects.filter(user=request.user)
	if not item:
	    item = Subscription(user=request.user)
	    item.save()
	else: item = item[0]
	item.tags = '%s%s'%(''.join(['%s, '%tag.name for tag in item.tags]), request.POST['tags'])
    r.write("<result><msg>success</msg></result>")
    return r

@login_required
@require_http_methods('GET')
def tnx(request, the_id):
    tnx = request.user.attrs.get('thanks', [])
    if the_id in tnx:
	return _fail()
    t = Topic.objects.filter(pk=the_id)
    if not t:
	return _fail()
    t = t[0]
    t.attrs['thanks'] = t.attrs.get('thanks', 0) + 1
    t.save()
    tnx.append(t.id)
    request.user.attrs['thanks'] = tnx
    request.user.save()
    r = HttpResponse(mimetype="text/xml")
    r.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>")
    r.write("<result><msg>success</msg><number>%s</number></result>"%t.attrs.get('thanks', 0))
    return r

@require_http_methods('GET')
def tags(request, tag=None):
    from tagging.models import TaggedItem
    result = TaggedItem.objects.get_by_model(Topic, tag).filter(approved=True).order_by('-created')
    if not result:
	raise Http404("No such tag")
    related_tags = []
    for item in result:
	for t in item.tags:
	    if t not in related_tags and t.name != tag:
		related_tags.append(t)
    q = get_page(request.GET.get('page', 0), 
	QuerySetPaginator(result, RESULTS_ON_PAGE, orphans=5),
    )

    return render_to_response('tags.html', {
	'result': q,
	'related_tags': related_tags,
	'tag': tag,
	'title': u"%s %s"%(_("tag"), tag)
    })

def upload_scr(request, the_id=0):
    topic = get_object_or_404(Topic, pk=the_id)
    if request.method == 'POST':
	form = ScreenshotForm(topic, request.POST, request.FILES)
	if form.is_valid():
	    form.save()
    else:
	form = ScreenshotForm(topic)
    return render_to_response('upload_scr_form.html', {
	'form': form,
    })
