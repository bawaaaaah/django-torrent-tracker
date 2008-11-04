#!/usr/bin/python
import sys, os
sys.path.append('/home/grey/src/df')
from fs.models import Topic, SECTIONS, AKINDS, BKINDS, GKINDS, MKINDS, OKINDS, PKINDS, TKINDS
from stats.models import Sections

from django.db.models import Q

for s in SECTIONS+AKINDS+BKINDS+GKINDS+MKINDS+OKINDS+PKINDS+TKINDS:
    i, created = Sections.objects.get_or_create(cat=s[0])
    i.cnt = Topic.objects.filter(Q(section=s[0])|Q(subcat=s[0])).count()
    i.save()
    
for r in Sections.objects.all():
    print r.cat, ': ', r.cnt
