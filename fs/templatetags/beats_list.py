#from django.contrib.sites.models import Contact
from fs.models import Topic
from django.template import Library,Node
register = Library()

class BeatsObject(Node):
    def render(self, context):
	if context.has_key('object'):
	    if context['object']:
		if context['object'].attrs.has_key('beats'):
		    context['beats'] = Topic.objects.filter(pk__in=context['object'].attrs['beats']).order_by('-created')
	return ''

register.tag('get_beats', lambda parser, token: BeatsObject())
