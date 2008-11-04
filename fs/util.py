import datetime

from fs.models import Topic
from utils import order_by

def sort_result(ids, peers, asc=False, by_seeds=True, limit=0):
    # sort Topic objects by seeds or leechers
    now = datetime.datetime.now()
    lst = [] #[torrent_id, number of seeds]
    for i in ids:
	if by_seeds:
	    lst.append((i, len([p for p in peers if p['torrent_id'] == i and p['left'] == 0 and p['expire_time']>now])))
	else:
	    lst.append((i, len([p for p in peers if p['torrent_id'] == i and p['left'] > 0 and p['expire_time']>now])))

    if not asc:
	lst = order_by(lst, [1], [1])
    else:
    	lst = order_by(lst, [1], [])

    if lst:
	return Topic.objects.filter(torrent__id__in=[i[0] for i in lst])[:limit]
    else:
	return []
