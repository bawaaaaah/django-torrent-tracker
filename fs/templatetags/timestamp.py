import datetime
from django import template
register = template.Library()

@register.filter(name="timestamp")
def format(date, string=None):
    if string:
        result = datetime.date.fromtimestamp(date).strftime(string)
    else:
	result = datetime.date.fromtimestamp(date).strftime('%Y-%m-%d')
    return result
