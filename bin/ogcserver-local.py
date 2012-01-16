#!/usr/bin/env python

import os
import sys
import socket
from os import path

if not len(sys.argv) > 1:
    sys.exit('Usage: %s <map.xml>' % os.path.basename(sys.argv[0]))

sys.path.insert(0,os.path.abspath('.'))

from ogcserver.wsgi import WSGIApp

application = WSGIApp('conf/ogcserver.conf',mapfile=sys.argv[1])

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    #if os.uname()[0] == 'Darwin':
    #   host = socket.getfqdn() # yourname.local
    #else:
    #   host = '0.0.0.0'
    host = '0.0.0.0'
    port = 8000
    httpd = make_server(host, port, application)
    print "Listening at %s:%s...." % (host,port)
    httpd.serve_forever()
