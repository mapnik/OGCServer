from ogcserver.cgiserver import Handler
from jon import fcgi

class OGCServerHandler(Handler):
    configpath = '/path/to/ogcserver.conf'

fcgi.Server({fcgi.FCGI_RESPONDER: OGCServerHandler}).run()
