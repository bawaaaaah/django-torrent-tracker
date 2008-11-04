from kaa import metadata
import os, sys
import chardet
from utils import slughifi
import magic

class Meta(object):
    def __init__(self, path):
	self.info = {}
	try:
	    info = metadata.parse(os.path.normpath(path))
	except:
	    sys.stderr.write("METADATA, problem with %s" % path)
	    return
	if not info:
	    self.info = {}
	    return
	if not hasattr(info, 'mime'):
	    self.info = {}
	    return
	if not info.mime:
	    self.info = {}
	    return
	self.mime = info.mime
	
	if info.mime not in mimes: mimes.append(info.mime)
	
	if info.mime == 'audio/wav':
	    self.info = {'samplerate': info.samplerate}
	    self.icon = 'icon-snd'
        elif info.mime.startswith('audio') or info.mime.endswith('ogg'):
	    self.icon = 'icon-snd'
	    try:
		pattern=""
		if info.has_key('title'):
		    if info.title:
			title = info.title.encode("latin_1")
			pattern+=title
		if info.has_key('artist'):
		    if info.artist:
			artist = info.artist.encode("latin_1")
		        pattern+=" "+artist
		if info.has_key('album'):
		    if info.album:
			album = info.album.encode("latin_1")
			pattern+=" "+album
		if info.has_key('comment'):
		    if len(info.comment) > 0:
			comment = info.comment.encode("latin_1")
			pattern+=" "+comment
		if pattern:
		    enc = chardet.detect(pattern)['encoding']
		    if enc == 'EUC-TW' or enc == 'windows-1255' or enc == 'MacCyrillic' or enc == 'TIS-620' or enc == 'KOI8-R' or enc == 'IBM866':
			enc = 'CP1251'
		    elif not enc or enc.startswith('ISO-8859'):
			enc = "latin1"
		else:
		    enc = None
	    except:
		if info.has_key('title'):
		    if info.title:
			title = slughifi(info.title)
		if info.has_key('artist'):
		    if len(info.artist) > 0:
			artist = slughifi(info.artist)
		if info.has_key('album'):
		    if info.album:
			album = slughifi(info.album)
		if info.has_key('comment'):
		    if info.comment:
			comment = slughifi(info.comment)
		enc = None

	    for key in ['samplerate', 'date', 'bitrate', 'trackno']:
		if hasattr(info, i):
		    self.info[key] = getattr(info, key)
	    if hasattr(info, 'length'):
		self.info['length'] = info.length # getPlayTimeString(value)
	    if hasattr(info, 'comment'):
		try:
		    tmp=value.encode("latin_1")
		    try:
			tmp = unicode(tmp, chardet.detect(tmp)['encoding'])
		    except:
			tmp=re.sub('[^a-zA-Z0-9\\s\\-]{1}', replace_char, value).lower()
		except:
		    tmp=re.sub('[^a-zA-Z0-9\\s\\-]{1}', replace_char, value).lower()
		if re.sub('\s+','',tmp):
		    self.info['comment'] = tmp

		if hasattr(info, 'album') and enc:
		    try:
			self.info['album'] = unicode(album, enc)
		    except UnicodeEncodeError:
			self.info['album'] = slughifi(album)
		if hasattr(info, 'artist') and enc:
		    try:
			self.info['artist'] = unicode(artist, enc)
		    except UnicodeEncodeError:
			self.info['artist'] = slughifi(artist)
		if hasattr(info, 'title') and enc:
		    try:
			self.info['title'] = unicode(title, enc)
		    except UnicodeEncodeError:
			self.info['title'] = slughifi(title)

	elif info.mime.startswith('video') or \
	    info.mime == 'application/ogm' or \
	    info.mime == 'application/mkv':
	    if info.mime.endswith('x-msvideo'): self.icon = 'icon-avi'
	    else: self.icon = 'icon-vid'
	    for key in ['comment', 'producer', 'genre', 'country']:
		if hasattr(info, key):
		    self.info[key] = getattr(info, key)
	    if hasattr(info, 'length'):
		self.info['length'] = info.length #getPlayTimeString(value)
	    if hasattr(info, 'all_header'):
		if len(info.all_header) > 0:
		    for k in info.all_header[0]:
			self.info[k] = info.all_header[0][k]
	    try:
		if info.video[0].codec:
		    self.info['codec'] = info.video[0].codec
		if info.video[0].fps:
		    self.info['fps'] = "%.0d" % info.video[0].fps
		if info.video[0].width:
		    self.info['width'] = info.video[0].width
		if info.video[0].height:
		    self.info['height'] = info.video[0].height
		if info.header['INFO']['ISRC']:
		    self.info['source'] = info.header['INFO']['ISRC']
	    except:
		pass
	#for j in self.info.keys():
	    #self.info[j] = unicode(self.info[j]).encode("UTF-8")

    def setTags(self, tags):
	"""
	Takes tags as dictionary
	"""
	if self.mime == 'application/ogg':
	    try:
		#python-pyvorbis required
		import ogg.vorbis
	    except:
		return
	    OggInfoTag=ogg.vorbis.VorbisComment()
    	    try:
		for name in tags:
		    OggInfoTag.add_tag(name,tags[name])
		    OggInfoTag.write_to(self.path)
	    except:
		pass
	elif self.mime.startswith('audio') and self.mime != 'audio/wav':
	    import eyeD3
	    tag = eyeD3.Tag()
	    tag.link(self.path)
	    for name in tags:
		if name == 'TITLE':
		    tag.setTitle(tags[name])
		elif name == 'ALBUM':
		    tag.setAlbum(tags[name])
		elif name == 'ARTIST':
		    tag.setArtist(tags[name])
		elif name == 'DATE':
		    tag.setDate(tags[name])
		elif name == 'GENRE':
		    tag.setDate(tags[name])
		elif name == 'COMMENT':
            	    tag.addComment(tags[name])
		elif name == 'LYR':
		    tag.addLyrics(tags[name])
		tag.update()


class Path(object):
    def __str__(self):
	return self.name

    def getrelpath(self):
	return '/'.join(self.name.split(FTP_HOMEDIR+'/')[1].split('/')[1:])

    relpath = property(
        getrelpath, None, None,
        """ relative path for web
        """)

    def __init__(self, name):
	self.name = name
	self.isdir = os.path.isdir(self.name)
	if self.isdir:
	    self.icon = 'icon-dir'
	    return
	else:
	    try:
    		mi = magic.open(magic.MAGIC_MIME)
		mi.load()
		f = file(name, "r")
		buffer = f.read(4096)
		f.close()
		kind =  mi.buffer(buffer)
		mi.close()
	    except:
		self.icon = 'icon-unk'
		return
	if not kind:
	    self.icon = 'icon-unk'
	    return
	if kind.endswith('msword'):
	    self.icon = 'icon-doc'
	elif kind.startswith('text'):
	    self.icon = 'icon-txt'
	elif kind.startswith('image'):
	    self.icon = 'icon-png'
	elif kind.endswith('debian-package'):
	    self.icon = 'icon-deb'
	elif kind.endswith('iso9660'):
	    self.icon = 'icon-iso'
	elif kind.endswith('stuffit'):
	    self.icon = 'icon-stf'
	elif kind.endswith('x-rar'):
	    self.icon = 'icon-rar'
	elif kind.endswith('x-zip'):
	    self.icon = 'icon-zip'
	elif kind.endswith('zip') or kind.endswith('zip2'):
	    self.icon = 'icon-tgz'
	elif kind.endswith('x-tar'):
	    self.icon = 'icon-tar'
	elif kind.endswith('pdf'):
	    self.icon = 'icon-pdf'
	elif kind.startswith('app'):
	    self.icon = 'icon-app'
	else:
	    self.icon = 'icon-unk'

