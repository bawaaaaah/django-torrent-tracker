from django.template import Library, Node
from fs.models import Topic
register = Library()

class BulletinObject(Node):
    def render(self, context):
	if not context.has_key('post'):
	    return ''
	context['bulletin'] = Topic.objects.filter(section=context['post'].section, approved=True).exclude(id=context['post'].id)[:5]
	return ''

register.tag('get_bulletin', lambda parser, token: BulletinObject())
