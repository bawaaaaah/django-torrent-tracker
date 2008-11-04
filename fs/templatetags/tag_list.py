#from django.contrib.sites.models import Contact
from tagging.models import Tag
from fs.models import Topic, SECTIONS
from django.template import Library,Node
register = Library()

class TagListObject(Node):
    def render(self, context):
	post = context.get('post')
	if post:
	    context['tags'] = Tag.objects.usage_for_model(Topic, filters=dict(pk=context['post'].id), counts=True)
	    return ''
	if not context.has_key('slug'):
	    context['tags'] = Tag.objects.usage_for_model(Topic, counts=True)
	    return ''
	if context['slug'] not in [i[0] for i in SECTIONS]:
	    context['tags'] = []
	    return ''
	context['tags'] = Tag.objects.usage_for_model(Topic, filters=dict(section=context['slug']), counts=True)
	return ''

register.tag('get_taglist', lambda parser, token: TagListObject())
