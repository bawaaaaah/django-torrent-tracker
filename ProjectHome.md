torrent tracker, which uses memcache library for storing peers

**bugs**:
```
* parser of search queries, say, not perfect
* multilanguage search does not work
```

**requirements**
```
* python-beautifulsoup 
   tested with 3.0.4
* cmemcache
   tested with 0.91
* python-imaging
   tested with 1.16
* django-tagging: http://code.google.com/p/django-tagging/
* kaa.metadata: svn://svn.freevo.org/kaa/trunk
  (seems it is working only with python 2.4 at the moment)
```

**optional**
```
* solr, if you want search engine
```

**incomplete features**

```
* uploading video on ftp and automatic video transoding to .flv
```

screenshots: http://imgrey.0xdf.net/django-torrent-tracker/
