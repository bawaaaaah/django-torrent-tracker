from cPickle import dumps, loads
import os.path

from django.core.cache import cache
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import Http404, HttpResponse
from django.views.decorators.http import require_http_methods

from utils import HttpResponseRedirect
from settings import FTP_HOMEDIR,DATABASE_NAME, DATABASE_USER, DATABASE_PASSWORD
from transcoding.forms import *
from transcoding.models import *
from users.views import login_required
from fs.models import Topic

def _store(value):
    import random
    from string import letters
    key = ''.join(random.sample(letters, 16))
    cache.set(key, value, 1800)
    return key
 
def _locate(item, list, rel=False):
    if rel:
	for i in xrange(len(list)):
	    if item == unicode(list[i].relpath, 'UTF-8'):
		return True
    else:
	for i in xrange(len(list)):
	    if item == unicode(list[i], 'UTF-8'):
		return True
    return False

def _ls(cur, username, path, walk=False):
    if path.endswith('/'): path = path[:-1]
    if not path.startswith('/'): path = '/'+path
    if not walk:
	ls = ({'dirnames': [], 'filenames': []}, '/')
    else: ls = []
    cur.execute("SELECT ls FROM transcoding_fs WHERE path=%s AND username=%s LIMIT 1", (path, username))
    stuff = cur.fetchone()
    if not stuff:
	return ls
    if not walk:
	stuff = loads(str(stuff[0]))
	return (stuff, path)
    ls = loads(str(stuff[0]))
    result = ls['filenames']
    for d in ls['dirnames']:
	result += list(_ls(cur, username, d.split(os.path.join(FTP_HOMEDIR, username))[1], walk=True))
    return result

def _connect():
    import psycopg2 as psycopg
    con = psycopg.connect(database=DATABASE_NAME, user=DATABASE_USER, password=DATABASE_PASSWORD, host='127.0.0.1')
    cur = con.cursor()
    return (con, cur)

@login_required
@require_http_methods('GET')
def chdir(request, path='/'):
    try:
	con, cur = _connect()
	lst, path = _ls(cur, request.user.username, path)
	con.close()
    except:
	lst, path = {'dirnames': [], 'filenames': []}, '/'
    form = FilesForm(lst, _store((lst, path)))
    return render_to_response('transcoding/ftp.html', {
	'ls': lst,
	'path': path,
	'form': form,
    }, context_instance=RequestContext(request))

@login_required
@require_http_methods('GET')
def tq_ls(request):
    q = Queue.objects.filter(user=request.user)
    if q:
	qform = TQForm(q, _store([i.id for i in q]))
    else:
	qform = None
    return render_to_response('transcoding/transcoding.html', {
	'qform': qform,
	'user': request.user,
	'not_approved': Topic.objects.filter(author=request.user, approved=False)
    })

@login_required
@require_http_methods('POST')
def add(request):
    form = TQForm(None, None, request.POST)
    if not form.is_valid():
	return HttpResponse("You've submitted invalid or expired form.")
    stuff = cache.get(form.cleaned_data['key'])
    cache.delete(form.cleaned_data['key'])
    if not stuff:
	return HttpResponse("You've submitted invalid or expired form.")
    form = TQForm(Queue.objects.filter(pk__in=stuff), None, request.POST)
    if form.is_valid():
	s = [int(f.split('_')[1]) for f in form.cleaned_data.iterkeys() if form.cleaned_data[f] and f != 'key']
	if s:
	    for q in Queue.objects.filter(pk__in=[stuff[i] for i in s]):
		q.order = form.cleaned_data['q_%d'%stuff.index(q.id)][:9]
		try:
		    the_id = int(form.cleaned_data['t_%d'%stuff.index(q.id)])
		except ValueError:
		    the_id = 0
		if the_id:
		    t = Topic.objects.filter(id=the_id)
		    if t:
			q.topic = t[0]
		q.save()
    return HttpResponseRedirect('/tq/')

@login_required
@require_http_methods('POST')
def file(request):
    form = FilesForm(None, None, request.POST)
    if not form.is_valid():
	return HttpResponse("Something wrong with submitted form.")
    stuff = cache.get(form.cleaned_data['key'])
    cache.delete(form.cleaned_data['key'])
    if not stuff:
	return HttpResponse("You have submitted invalid or expired form.")
    form = FilesForm({'filenames': stuff[0]['filenames'], 'dirnames': stuff[0]['dirnames']}, None, request.POST)
    if not form.is_valid():
	return HttpResponse("You have submitted invalid or expired form.")
    lst = [int(f.split('_')[1]) for f in form.cleaned_data.iterkeys() if form.cleaned_data[f] == True]
    if len(lst) == 0:
	return HttpResponseRedirect('/tq/')
    result = []
    items = stuff[0]['dirnames']+stuff[0]['filenames']
    con, cur = _connect()
    for n in lst:
	if type(items[n]) in [unicode, str]:
	    result += _ls(cur, request.user.username, items[n].split('%s/%s'%(FTP_HOMEDIR, request.user.username))[1], walk=True)
	else:
	    result.append(items[n])
    con.close()
    if not result:
	return HttpResponseRedirect('/tq/')
    fnames = [f.name for f in result]
    q = Queue.objects.filter(file__in=fnames)
    for i in result[:]:
	if i.name in [j.file for j in q]:
	    result.remove(i)
    for f in result:
	e = Queue(status='pending')
	e.user = request.user
	e.file = f.name
	e.attrs['obj'] = f
	e.save()
    return HttpResponseRedirect('/tq/')


