import nose

def start_response_111(status, headers):
    for header in headers:
        if header[0] == 'Content-Type':
            assert header[1] == 'application/vnd.ogc.wms_xml'
    assert status == '200 OK'

def start_response_130(status, headers):
    for header in headers:
        if header[0] == 'Content-Type':
            assert header[1] == 'text/xml'
    assert status == '200 OK'

def start_response_check_404(status, headers):
    print('status code: %s' % status)
    assert status == '404 NOT FOUND'

def get_wsgiapp():
    import os
    from ogcserver.wsgi import WSGIApp
    base_path, tail = os.path.split(__file__)
    wsgi_app = WSGIApp(os.path.join(base_path, 'ogcserver.conf'))
    return wsgi_app

def get_environment():
    environ = {}
    environ['HTTP_HOST'] = "localhost"
    environ['SCRIPT_NAME'] = __name__
    environ['PATH_INFO'] = '/'
    return environ

def test_get_capabilities():
    wsgi_app = get_wsgiapp()
    environ = get_environment()
    environ['QUERY_STRING'] = "EXCEPTION=application/vnd.ogc.se_xml&VERSION=1.1.1&SERVICE=WMS&REQUEST=GetCapabilities&"
    response = wsgi_app.__call__(environ, start_response_111)
    content = ''.join(response)

    environ['QUERY_STRING'] = "EXCEPTION=application/vnd.ogc.se_xml&VERSION=1.3.0&SERVICE=WMS&REQUEST=GetCapabilities&"
    response = wsgi_app.__call__(environ, start_response_130)
    ''.join(response)

def test_bad_query():
    wsgi_app = get_wsgiapp()
    environ = get_environment()
    environ['QUERY_STRING'] = "EXCEPTION=application/vnd.ogc.se_xml&VERSION=1.1.1&SERVICE=WMS&REQUEST=GetMap&"
    response = wsgi_app.__call__(environ, start_response_check_404)
    environ['QUERY_STRING'] = "EXCEPTION=application/vnd.ogc.se_xml&VERSION=1.3.0&SERVICE=WMS&REQUEST=GetMap&"
    response = wsgi_app.__call__(environ, start_response_check_404)
