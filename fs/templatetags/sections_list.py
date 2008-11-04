from fs.models import Topic, SECTIONS, AKINDS, BKINDS, GKINDS, MKINDS, \
    OKINDS, PKINDS, TKINDS, get_cat
from stats.models import Sections
from django.template import Library, Node
register = Library()

class SectionsListObject(Node):
    """
    returning the following: 
    { category: [
	    count, 'full category name',
	    {subcat: (subcat name, subcat count)}
	]
    }
    """
    def render(self, context):
	result = {}
	stats = Sections.objects.filter(cnt__gt=0)
	cats = [i[0] for i in SECTIONS]
	names = dict(SECTIONS)
	for r in stats:
	    if r.cat not in cats:
		continue
	    result[r.cat] = [r.cnt, names[r.cat]]

	t = dict(AKINDS+BKINDS+GKINDS+MKINDS+OKINDS+PKINDS+TKINDS)
	for r in stats:
	    ccat = get_cat(r.cat)
	    if r.cat in cats:
		continue
	    item = result.get(ccat)
	    if not item:
		continue
	    v = {r.cat: (t.get(r.cat), r.cnt)}
	    if len(item) > 2:
		item[2].update(v)
	    else:
		item.append(v)
	    result[ccat] = item
	context['cat_tree'] = result
	return ''

register.tag('get_sectionslist', lambda parser, token: SectionsListObject())
