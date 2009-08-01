from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.template.defaultfilters import striptags
from django.utils import simplejson
from django.utils.translation import ugettext as _

from board.models import Post, WatchList, AbuseReport, PermissionError, UserBan
from board.templatetags.extras import render_filter

import datetime

def _sanitize(text):
    return render_filter(striptags(text), "safe")


def rpc_post(request):
    try:
        show_id = int(request.GET.get('show'))
        orig_id = int(request.GET.get('orig'))
    except (ValueError, TypeError):
        return HttpResponse('')
    post = Post.objects.get(pk=show_id)
    if not post.thread.category.can_read(request.user):
        raise PermissionError

    prev_id = ''
    rev_id = ''
    if post.revision is not None:
        rev_id = str(post.revision.id)
    if post.previous is not None:
        prev_id = str(post.previous.id)

    resp = {'text': _sanitize(post.text),
            'username': post.attrs.get('editor', post.user).name,
            'prev_id': prev_id,
            'rev_id': rev_id,
            'thread_id': post.thread.id,
            'notice': _("This message has been revised"),
            }
    return HttpResponse(simplejson.dumps(resp), mimetype='application/javascript')


def rpc_preview(request):
    text = request.raw_post_data 
    return HttpResponse(simplejson.dumps({'preview': _sanitize(text)}),
            mimetype='application/javascript')


def rpc_lookup(request, queryset, field, limit=5):
    # XXX We should probably restrict member (or other) lookups to registered users
    obj_list = []
    if request.GET.get('query', None):
        lookup = { '%s__icontains' % field: request.GET['query'],}
        for obj in queryset.filter(**lookup)[:limit]:
            obj_list.append({"id": obj.id, "name": getattr(obj, field)})
    object = {"ResultSet": { "total": str(limit), "Result": obj_list } }
    return HttpResponse(simplejson.dumps(object), mimetype='application/javascript')


def _toggle_boolean_field(object, field):
    """
    Switches the a boolean value and returns the new value.
    object should be a Django Model
    """
    setattr(object, field, (not getattr(object, field)))
    object.save()
    return getattr(object, field)


def rpc_csticky(request, **kwargs):
    if not request.user.is_staff:
        raise PermissionDenied
    if _toggle_boolean_field(kwargs['thread'], 'csticky'):
        return {'link':_('unset csticky'), 'msg':_('This thread is sticky in its category.')}
    else:
        return {'link':_('set csticky'), 'msg':_('Removed thread from category sticky list')}


def rpc_gsticky(request, **kwargs):
    if not request.user.is_staff:
        raise PermissionDenied
    if _toggle_boolean_field(kwargs['thread'], 'gsticky'):
        return {'link':_('unset gsticky'), 'msg':_('This thread is now globally sticky.')}
    else:
        return {'link':_('set gsticky'), 'msg':_('Removed thread from global sticky list')}


def rpc_close(request, **kwargs):
    if not request.user.is_staff:
        raise PermissionDenied
    if _toggle_boolean_field(kwargs['thread'], 'closed'):
        return {'link':_('open thread'), 'msg':_('This discussion is now CLOSED.')}
    else:
        return {'link':_('close thread'), 'msg':_('This discussion is now OPEN.')}


def rpc_watch(request, **kwargs):
    thr = kwargs['thread']
    if not thr.category.can_read(request.user):
        raise PermissionError
    try:
        # it exists, stop watching it
        wl = WatchList.objects.get(user=request.user, thread=thr)
        wl.delete()
        return {'link':_('watch'),
                'msg':_('This thread has been removed from your favorites.')}
    except WatchList.DoesNotExist:
        # create it
        wl = WatchList(user=request.user, thread=thr)
        wl.save()
        return {'link':_('dont watch'),
                'msg':_('This thread has been added to your favorites.')}


def rpc_abuse(request, **kwargs):
    # TODO: test this
    abuse = AbuseReport.objects.get_or_create(
            submitter = request.user,
            post = kwargs['post'],
            )
    return {'link': '',
            'msg':_('The moderators have been notified of possible abuse')}


def rpc_censor(request, **kwargs):
    if not request.user.is_staff:
        raise PermissionDenied
    if _toggle_boolean_field(kwargs['post'], 'censor'):
        return {'link':_('uncensor'), 'msg':_('This post is censored!')}
    else:
        return {'link':_('censor'), 'msg':_('This post is no longer censored.')}

def rpc_quote(request, **kwargs):
    post = Post.objects.select_related().get(id=kwargs['oid'])
    if not post.thread.category.can_read(request.user):
        raise PermissionError
    if post.is_private and post.user != request.user and not post.private.filter(id=request.user.id).count():
        raise PermissionDenied
    return {'text': post.text, 'author': unicode(post.user)}

def rpc_ban(request):
    """
    takes attrubutes: uid -- user id, expires -- date,
    reason -- the reason of ban
    """
    from users.models import User
    if not request.user.is_staff:
        raise PermissionDenied
    try:
        uid = int(request.GET.get('uid'))
        expires = int(request.GET.get('expires'))
    except (ValueError, TypeError):
        return HttpResponse('false')
    user = User.objects.filter(id=uid)
    if not user:
        return HttpResponse('false')
    if expires == -1:
        UserBan.objects.filter(user=user[0]).delete()
        return HttpResponse('true')
    ban, is_created = UserBan.objects.get_or_create(user=user[0])
    ban.reason = request.GET.get('reason', '')
    if expires in [30, 60, 180, 720, 1440, 10080]:
        ban.expires = datetime.datetime.now() + datetime.timedelta(
            minutes=expires)
    else:
        ban.expires = None
    ban.save()
    return HttpResponse('true')

# vim: ai ts=4 sts=4 et sw=4

