"""WSGI application wrapper for Mapnik OGC WMS Server."""

try:
    from urlparse import parse_qs
except ImportError:
    from cgi import parse_qs

import logging
import imp

from cStringIO import StringIO

import mapnik

from ogcserver.common import Version
from ogcserver.WMS import BaseWMSFactory
from ogcserver.configparser import SafeConfigParser
from ogcserver.wms111 import ExceptionHandler as ExceptionHandler111
from ogcserver.wms130 import ExceptionHandler as ExceptionHandler130
from ogcserver.exceptions import OGCException, ServerConfigurationError

def do_import(module):
    """
    Makes setuptools namespaces work
    """
    moduleobj = None
    exec 'import %s' % module 
    exec 'moduleobj=%s' % module
    return moduleobj
 
class WSGIApp:

    def __init__(self, configpath, mapfile=None,fonts=None,home_html=None):
        conf = SafeConfigParser()
        conf.readfp(open(configpath))
        # TODO - be able to supply in config as well
        self.home_html = home_html
        self.conf = conf
        if fonts:
            mapnik.register_fonts(fonts)
        if mapfile:
            wms_factory = BaseWMSFactory(configpath)
            # TODO - add support for Cascadenik MML
            wms_factory.loadXML(mapfile)
            wms_factory.finalize()
            self.mapfactory = wms_factory
        else:
            if not conf.has_option_with_value('server', 'module'):
                raise ServerConfigurationError('The factory module is not defined in the configuration file.')
            try:
                mapfactorymodule = do_import(conf.get('server', 'module'))
            except ImportError:
                raise ServerConfigurationError('The factory module could not be loaded.')
            if hasattr(mapfactorymodule, 'WMSFactory'):
                self.mapfactory = getattr(mapfactorymodule, 'WMSFactory')()
            else:
                raise ServerConfigurationError('The factory module does not have a WMSFactory class.')
        if conf.has_option('server', 'debug'):
            self.debug = int(conf.get('server', 'debug'))
        else:
            self.debug = 0
        if self.conf.has_option_with_value('server', 'maxage'):
            self.max_age = 'max-age=%d' % self.conf.get('server', 'maxage')
        else:
            self.max_age = None

    def __call__(self, environ, start_response):
        reqparams = {}
        base = True
        for key, value in parse_qs(environ['QUERY_STRING'], True).items():
            reqparams[key.lower()] = value[0]
            base = False

        if self.conf.has_option_with_value('service', 'baseurl'):
            onlineresource = '%s' % self.conf.get('service', 'baseurl')
        else:
            # if there is no baseurl in the config file try to guess a valid one
            onlineresource = 'http://%s%s%s?' % (environ['HTTP_HOST'], environ['SCRIPT_NAME'], environ['PATH_INFO'])

        try:
            if not reqparams.has_key('request'):
                raise OGCException('Missing request parameter.')
            request = reqparams['request']
            del reqparams['request']
            if request == 'GetCapabilities' and not reqparams.has_key('service'):
                raise OGCException('Missing service parameter.')
            if request in ['GetMap', 'GetFeatureInfo']:
                service = 'WMS'
            else:
                try:
                    service = reqparams['service']
                except:
                    service = 'WMS'
                    request = 'GetCapabilities'
            if reqparams.has_key('service'):
                del reqparams['service']
            try:
                ogcserver = do_import('ogcserver')
            except:
                raise OGCException('Unsupported service "%s".' % service)
            ServiceHandlerFactory = getattr(ogcserver, service).ServiceHandlerFactory
            servicehandler = ServiceHandlerFactory(self.conf, self.mapfactory, onlineresource, reqparams.get('version', None))
            if reqparams.has_key('version'):
                del reqparams['version']
            if request not in servicehandler.SERVICE_PARAMS.keys():
                raise OGCException('Operation "%s" not supported.' % request, 'OperationNotSupported')
            ogcparams = servicehandler.processParameters(request, reqparams)
            try:
                requesthandler = getattr(servicehandler, request)
            except:
                raise OGCException('Operation "%s" not supported.' % request, 'OperationNotSupported')

            # stick the user agent in the request params
            # so that we can add ugly hacks for specific buggy clients
            ogcparams['HTTP_USER_AGENT'] = environ.get('HTTP_USER_AGENT', '')

            response = requesthandler(ogcparams)
        except:
            version = reqparams.get('version', None)
            if not version:
                version = Version()
            else:
                version = Version(version)
            if version >= '1.3.0':
                eh = ExceptionHandler130(self.debug,base,self.home_html)
            else:
                eh = ExceptionHandler111(self.debug,base,self.home_html)
            response = eh.getresponse(reqparams)
        response_headers = [('Content-Type', response.content_type),('Content-Length', str(len(response.content)))]
        if self.max_age:
            response_headers.append(('Cache-Control', self.max_age))
        start_response('200 OK', response_headers)
        yield response.content


#  PasteDeploy factories [kiorky kiorky@cryptelium.net]

class BasePasteWSGIApp(WSGIApp):
    def __init__(self,
                 configpath,
                 fonts=None,
                 home_html=None,
                 **kwargs
                ):
        conf = SafeConfigParser()
        conf.readfp(open(configpath))
        # TODO - be able to supply in config as well
        self.home_html = home_html
        self.conf = conf
        if fonts:
            mapnik.register_fonts(fonts)
        if 'debug' in kwargs:
            self.debug = bool(kwargs['debug'])
        else:
            self.debug = False
        if self.debug:
            self.debug=1
        else:
            self.debug=0
        if 'maxage' in kwargs:
            self.max_age = 'max-age=%d' % kwargs.get('maxage')
        else:
            self.max_age = None

class MapFilePasteWSGIApp(BasePasteWSGIApp):
    def __init__(self,
                 configpath,
                 mapfile,
                 fonts=None,
                 home_html=None,
                 **kwargs
                ):
        BasePasteWSGIApp.__init__(self, 
                                  configpath, 
                                  font=fonts, home_html=home_html, **kwargs)
        wms_factory = BaseWMSFactory(configpath)
        wms_factory.loadXML(mapfile)
        wms_factory.finalize()
        self.mapfactory = wms_factory

class WMSFactoryPasteWSGIApp(BasePasteWSGIApp):
    def __init__(self,
                 configpath,
                 server_module,
                 fonts=None,
                 home_html=None,
                 **kwargs
                ):
        BasePasteWSGIApp.__init__(self, 
                                  configpath, 
                                  font=fonts, home_html=home_html, **kwargs)
        try:
            mapfactorymodule = do_import(server_module)
        except ImportError:
            raise ServerConfigurationError('The factory module could not be loaded.')
        if hasattr(mapfactorymodule, 'WMSFactory'):
            self.mapfactory = getattr(mapfactorymodule, 'WMSFactory')(configpath)
        else:
            raise ServerConfigurationError('The factory module does not have a WMSFactory class.')

def ogcserver_base_factory(base, global_config, **local_config):
    """
    A paste.httpfactory to wrap an ogcserver WSGI based application.
    """
    log = logging.getLogger('ogcserver.wsgi')
    wconf = global_config.copy()
    wconf.update(**local_config)
    debug = False
    if global_config.get('debug', 'False').lower() == 'true':
        debug = True
    configpath =  wconf['ogcserver_config']
    server_module =     wconf.get('mapfile', None)
    fonts =       wconf.get('fonts', None)
    home_html =   wconf.get('home_html', None)
    app = None
    if base == MapFilePasteWSGIApp:
        mapfile = wconf['mapfile']
        app = base(configpath,
                   mapfile,
                   fonts=fonts,
                   home_html=home_html,
                   debug=False)
    elif base == WMSFactoryPasteWSGIApp:
        server_module = wconf['server_module']
        app = base(configpath,
                   server_module,
                   fonts=fonts,
                   home_html=home_html,
                   debug=False)
    def ogcserver_app(environ, start_response):
        from webob import Request
        req = Request(environ)
        try:
            resp = req.get_response(app)
            return resp(environ, start_response)
        except Exception, e:
            if not debug:
                log.error('%r: %s', e, e)
                log.error('%r', environ)
                from webob import exc
                return exc.HTTPServerError(str(e))(environ, start_response)
            else:
                raise
    return ogcserver_app

def ogcserver_map_factory(global_config, **local_config):
    return ogcserver_base_factory(MapFilePasteWSGIApp,
                                  global_config,
                                  **local_config)

def ogcserver_wms_factory(global_config, **local_config):
    return ogcserver_base_factory(WMSFactoryPasteWSGIApp,
                                  global_config,
                                  **local_config)

