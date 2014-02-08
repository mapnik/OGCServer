#!/usr/bin/env python

import os
import sys
import socket
from os import path
from pkg_resources import *
import argparse

parser = argparse.ArgumentParser(description='Runs the ogcserver as WMS server')

parser.add_argument('mapfile', type=str, help='''
A XML mapnik stylesheet
''')

args = parser.parse_args()

sys.path.insert(0,os.path.abspath('.'))

from ogcserver.wsgi import WSGIApp
import ogcserver

default_conf = resource_filename(ogcserver.__name__, 'default.conf')
application = WSGIApp(default_conf,args.mapfile)

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
