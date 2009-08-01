# -*- coding: utf-8 -*-
'''
SNAPboard specific template tags.
'''
# TODO: moves tags in extras.py to this file
# This will prevent potential namespace conflicts with other applications

from django import template
from django.conf import settings

register = template.Library()

def truncatechars(text, chars=200):
	if len(text) < chars:
		return text
	try:
		last_space = text.rindex(' ', 0, chars)
		if last_space < chars // 5:
			raise ValueError
	except ValueError:
		return text[:chars - 1] + u'…'
	else:
		return text[:last_space] + u'…'
register.filter(truncatechars)

def get_first_post_text(thread, user):
    from board.models import Thread
    return Thread.view_manager.get_first_post_text(thread.id, user)
register.filter(get_first_post_text)

def get_thread_pages(post_count, ppp):
    from django.core.paginator import Paginator
    from users.templatetags.paginator import paginator
    if post_count <= 1:
	return None
    pages = []
    p = paginator({'result': Paginator(range(1, post_count), ppp).page(1)})
    if not p['in_leading_range']:
        for n in p['pages_outside_trailing_range']:
            pages.append(n)
	pages.append(None)
    for n in p['page_numbers']:
	pages.append(n)
    if not p['in_trailing_range']:
	pages.append(None)
	for n in p['pages_outside_leading_range']:
	    pages.append(n)
    return pages
register.filter(get_thread_pages)

def is_banned(user):
    from board.models import UserBan
    ban = UserBan.objects.filter(user=user)
    if ban:
	return ban[0]
    return []
register.filter(is_banned)
