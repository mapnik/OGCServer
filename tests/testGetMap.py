import nose
import os
from ogcserver.configparser import SafeConfigParser
from ogcserver.WMS import BaseWMSFactory
from ogcserver.wms111 import ServiceHandler as ServiceHandler111
from ogcserver.wms130 import ServiceHandler as ServiceHandler130
from ogcserver.common import ColorFactory

def _wms_services(mapfile):
    base_path, tail = os.path.split(__file__)
    file_path = os.path.join(base_path, mapfile)
    wms = BaseWMSFactory() 
    wms.loadXML(file_path)
    wms.finalize()

    conf = SafeConfigParser()
    conf.readfp(open(os.path.join(base_path, 'ogcserver.conf')))

    wms111 = ServiceHandler111(conf, wms, "localhost")
    wms130 = ServiceHandler130(conf, wms, "localhost")

    return (conf, {
        '1.1.1': wms111,
        '1.3.0': wms130
    })

def test_no_background_color():
    # load mapfile with no background-color definition
    conf, services = _wms_services('mapfile_encoding.xml')

    reqparams = {
        'srs': 'EPSG:4326',
        'bbox': '-180.0000,-90.0000,180.0000,90.0000',
        'width': 800,
        'height': 600,
        'layers': '__all__',
        'styles': '',
        'format': 'image/png',
    }

    from ogcserver.WMS import ServiceHandlerFactory
    mapfactory = BaseWMSFactory() 
    servicehandler = ServiceHandlerFactory(conf, mapfactory, '', '1.1.1')
    ogcparams = servicehandler.processParameters('GetMap', reqparams)
    ogcparams['crs'] = ogcparams['srs']
    ogcparams['HTTP_USER_AGENT'] = 'unit_tests'

    m = services['1.1.1']._buildMap(ogcparams)
    print 'wms 1.1.1 backgound color: %s' % m.background
    assert m.background == ColorFactory('rgb(255,255,255)')

    m = services['1.3.0']._buildMap(ogcparams)
    print 'wms 1.3.0 backgound color: %s' % m.background
    assert m.background == ColorFactory('rgb(255,255,255)')

def test_map_background_color():
    conf, services = _wms_services('mapfile_background-color.xml')

    reqparams = {
        'srs': 'EPSG:4326',
        'bbox': '-180.0000,-90.0000,180.0000,90.0000',
        'width': 800,
        'height': 600,
        'layers': '__all__',
        'styles': '',
        'format': 'image/png',
    }

    from ogcserver.WMS import ServiceHandlerFactory
    mapfactory = BaseWMSFactory() 
    servicehandler = ServiceHandlerFactory(conf, mapfactory, '', '1.1.1')
    ogcparams = servicehandler.processParameters('GetMap', reqparams)
    ogcparams['crs'] = ogcparams['srs']
    ogcparams['HTTP_USER_AGENT'] = 'unit_tests'

    m = services['1.1.1']._buildMap(ogcparams)
    print 'wms 1.1.1 backgound color: %s' % m.background
    assert m.background == ColorFactory('rgb(255,0,0)')

    m = services['1.3.0']._buildMap(ogcparams)
    print 'wms 1.3.0 backgound color: %s' % m.background
    assert m.background == ColorFactory('rgb(255,0,0)')

def test_url_background_color():
    conf, services = _wms_services('mapfile_background-color.xml')

    reqparams = {
        'srs': 'EPSG:4326',
        'bbox': '-180.0000,-90.0000,180.0000,90.0000',
        'width': 800,
        'height': 600,
        'layers': '__all__',
        'styles': '',
        'format': 'image/png',
        'bgcolor': '0x00FF00',
    }

    from ogcserver.WMS import ServiceHandlerFactory
    mapfactory = BaseWMSFactory() 
    servicehandler = ServiceHandlerFactory(conf, mapfactory, '', '1.1.1')
    ogcparams = servicehandler.processParameters('GetMap', reqparams)
    ogcparams['crs'] = ogcparams['srs']
    ogcparams['HTTP_USER_AGENT'] = 'unit_tests'

    m = services['1.1.1']._buildMap(ogcparams)
    print 'wms 1.1.1 backgound color: %s' % m.background
    assert m.background == ColorFactory('rgb(0,255,0)')

    m = services['1.3.0']._buildMap(ogcparams)
    print 'wms 1.3.0 backgound color: %s' % m.background
    assert m.background == ColorFactory('rgb(0,255,0)')

def test_url_background_color_transparent():
    conf, services = _wms_services('mapfile_background-color.xml')

    reqparams = {
        'srs': 'EPSG:4326',
        'bbox': '-180.0000,-90.0000,180.0000,90.0000',
        'width': 800,
        'height': 600,
        'layers': '__all__',
        'styles': '',
        'format': 'image/png',
        'bgcolor': '0x00FF00',
        'transparent': 'TRUE',
    }

    from ogcserver.WMS import ServiceHandlerFactory
    mapfactory = BaseWMSFactory() 
    servicehandler = ServiceHandlerFactory(conf, mapfactory, '', '1.1.1')
    ogcparams = servicehandler.processParameters('GetMap', reqparams)
    ogcparams['crs'] = ogcparams['srs']
    ogcparams['HTTP_USER_AGENT'] = 'unit_tests'

    m = services['1.1.1']._buildMap(ogcparams)
    print 'wms 1.1.1 backgound color: %s' % m.background
    assert m.background == None

    m = services['1.3.0']._buildMap(ogcparams)
    print 'wms 1.3.0 backgound color: %s' % m.background
    assert m.background == None
