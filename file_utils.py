import os, sys
import string
import random
import unicodedata
import chardet

def toUnicode(string):
    """
    Turns everything passed to it to unicode.
    """
    if isinstance(string, str):
        return unicode(string, 'utf8')
    elif isinstance(string, unicode):
        return unicode(string)
    elif string is None:
        return u''
    else:
        return unicode(str(string), 'utf8')

def mv2rand(path):
    ext = os.path.splitext(path)[1]
    if len(ext) > 4 or string.strip(ext, chars=string.letters+string.digits):
	ext = ''
    elif ext:
	ext = '.'+ext
    while (1):
	fn = ''.join(random.sample('AnswertoLifhUvadEyg42', 8))
	dst = os.path.join(os.path.dirname(path), "%s%s"%(fn, ext))
	if not os.path.exists(dst):
	    break
    try:
	os.rename(path, dst)
    except OSError:
	#insert report routine here
	raise
    return dst

def sanitize(path):
    """
    Try to represent in readable form the file name.
    We are expecting the absolute path.
    """
    #sys.stderr.write("\nsanitize() PATH: %s\n"%path)
    #from django.utils.encoding import force_unicode
    fn = os.path.basename(path)
    parent = os.path.dirname(path)
    try:
	#sys.stderr.write("ENCODING: %s\n"%enc)
	ext = os.path.splitext(fn)[1]
	if ext:
	    if len(ext) <= 4 and not string.strip(ext, chars=string.letters):
		if not string.strip(fn[:-len(ext)], chars=string.punctuation+string.whitespace):
		    return (mv2rand(path), True)
	enc = chardet.detect(fn)['encoding']
	if not enc or not string.strip(fn, chars=string.punctuation+string.whitespace):
	    return (mv2rand(path), True)
	if enc != 'utf-8' and enc != 'ascii':
	    alias = unicode(fn, enc)
	    dst = os.path.join(parent, alias)
	    try:
		os.rename(path, dst)
	    except OSError:
		sys.stderr.write("PATH: %s DST: %s"%(path, dst))
		raise
	    #if it's basename then turn aux flag on
	    #since we don't want this thread to repeat
	    #previous action which triggered by renaming
	    return (dst, True)
    except (UnicodeDecodeError, LookupError):
	alias = unicodedata.normalize('NFKD', unicode(fn, 'utf-8', 'ignore')).encode('ascii', 'ignore').strip().lower()
	alias = re.sub('[-\s]+', '-', alias)
	if not string.strip(alias, chars=string.punctuation+string.whitespace):
	    return (mv2rand(path), True)
	dst = os.path.join(parent, alias)
	if os.path.exists(dst):
	    return (mv2rand(path), True)
	try:
	    os.rename(path, dst)
	except OSError:
	    sys.stderr.write("PATH: %s DST: %s"%(path, dst))
	    raise
	return (dst,True)
    return (path, False)

