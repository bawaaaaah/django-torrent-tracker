from board.models import Category
from django.template import Library,Node
register = Library()

class CatListObject(Node):
    def render(self, context):
	context['cat_list'] = [c for c in Category.objects.all().order_by('id') if c.can_view(context['user'])]
	return ''

register.tag('get_cat_list', lambda parser, token: CatListObject())
