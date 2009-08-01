def log(s, m='w'):
    f = open('/tmp/log', m)
    f.write('%s\n'%s)
    f.close()

def ulog(s):
    import codecs
    f = codecs.open('/tmp/log','w','UTF-8')
    f.write('%s'%s)
    f.close()

