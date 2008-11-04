from django import template

register = template.Library()

@register.filter(name="chk")
def chk(item, val):
    #the chain from chk() returning
    #None when there's 'item' in chain
    if item == val or not item:
	return None
    return item

@register.filter(name="key")
def key(d, k):
    from fields import Dict
    if type(d) is dict or type(d) is Dict:
	if d.has_key(k):
	    return d[k]
    return ''

@register.filter(name="empty")
def empty(dict):
    for k in dict.keys():
	if len(dict[k]) > 0:
	    return False
    return True

@register.filter(name="equal")
def equal(item, value):
    if str(item) == str(value):
	return True
    return False

@register.filter(name="lt")
def lt(item, value):
    if not item or not value: return True
    item = int(item)
    value = int(value)
    if item<value:
	return True
#    elif item>value:
#	return False
    return False

@register.filter(name="le")
def le(item, value):
    if not item or not value: return True
    item = int(item)
    value = int(value)
    if item<=value:
	return True
    return False

@register.filter(name="gt")
def gt(item, value):
    if not item or not value: return False
    item = int(item)
    value = int(value)
    if item>value:
	return True
    return False

@register.filter(name="gte")
def gte(item, value):
    if not item or not value: return False
    item = int(item)
    value = int(value)
    if item>=value:
	return True
    return False

@register.filter(name="divtwo")
def divtwo(number):
    if number%2:
	return True
    else:
	return False

@register.filter(name="retr")
def retr(lst, i):
    #retrieve element rfrom list
    if type(lst) is not list and type(lst) is not tuple:
	return ''
    try:
	i = int(i)
	return lst[i]
    except ValueError, IndexError:
	return ''

@register.filter(name="length")
def length(lst):
    from django.db.models.query import QuerySet
    if type(lst) is not list and type(lst) is not tuple and type(lst) is not QuerySet:
	return 0
    return len(lst)

@register.filter(name="strlen")
def strlen(text):
    return len(text)

@register.filter(name="truncate")
def truncate(ls, n):
    n = int(n)
    return ls[:n]

@register.filter(name="cut")
def cut(text, n):
    #cut out the number of words in supplied text
    try:
	n = int(n)
	return ' '.join(text.split(' ')[:n])
    except ValueError:
	return ' '.join(text.split(' ')[:42])

@register.filter(name="cutstr")
def cutstr(text, n):
    try:
	n = int(n)
	return text[:n]
    except ValueError:
	return text[:25]

@register.filter(name="words")
def words(text):
    return len(text.split(' '))

@register.filter(name="attr")
def attr(o, a):
    return getattr(o, a)

@register.filter(name="vfexists")
def vfexists(f):
    import os.path
    from settings import MEDIA_ROOT
    if os.path.exists(os.path.join(MEDIA_ROOT, 'flvs', f)):
	return True
    return False

#@register.filter(name="is_authenticated")
#def is_authenticated(user):
#    return user.is_authenticated()
 
@register.filter(name="inlist")
def inlist(lst, item):
    if not lst or not item: return False
    if item in lst: return True
    return False

@register.filter(name="yesno")
def yesno(item, var):
    from types import BooleanType
    if type(item) != str and type(item) != BooleanType:
	return ""
    if item:
	return var[0]
    else:
	var = var.split(',')
	if len(var) >1:
	    return var[1]
	else:
	    return ""

@register.filter(name="odd")
def odd(c):
    return c % 2

@register.filter(name="add_days")
def add_days(date, days):
    import datetime
    return date+datetime.timedelta(days=int(days))

@register.filter(name="is_expired")
def is_expired(date):
    import datetime
    if date>datetime.datetime.now():
	return False
    return True
