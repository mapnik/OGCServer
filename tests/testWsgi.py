import nose

def start_response_111(status, headers):
    for header in headers:
        if header[0] == 'Content-Type':
            assert header[1] == 'application/vnd.ogc.wms_xml'

def start_response_130(status, headers):
    for header in headers:
        if header[0] == 'Content-Type':
            assert header[1] == 'text/xml'

def test_get_capabilities():
    import os
    from ogcserver.wsgi import WSGIApp

    base_path, tail = os.path.split(__file__)

    wsgi_app = WSGIApp(os.path.join(base_path, 'ogcserver.conf'))

    environ = {}
    environ['QUERY_STRING'] = "EXCEPTION=application/vnd.ogc.se_xml&VERSION=1.1.1&SERVICE=WMS&REQUEST=GetCapabilities&"
    environ['HTTP_HOST'] = "localhost"
    environ['SCRIPT_NAME'] = __name__
    environ['PATH_INFO'] = '/'
    response = wsgi_app.__call__(environ, start_response_111)

    environ['QUERY_STRING'] = "EXCEPTION=application/vnd.ogc.se_xml&VERSION=1.3.0&SERVICE=WMS&REQUEST=GetCapabilities&"
    response = wsgi_app.__call__(environ, start_response_130)

    return True
 
