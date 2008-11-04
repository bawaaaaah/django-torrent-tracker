#!/usr/bin/python
import sys
sys.path.append('/home/grey/src/df')
from pysolr import Solr

conn = Solr('http://127.0.0.1:8080/solr/')
results = conn.search('author:"grey"')
for r in results:
    print r['id']
