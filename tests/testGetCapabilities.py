import nose
import os
from ogcserver.configparser import SafeConfigParser
from ogcserver.WMS import BaseWMSFactory
from ogcserver.wms111 import ServiceHandler as ServiceHandler111
from ogcserver.wms130 import ServiceHandler as ServiceHandler130

def _wms_capabilities():
    base_path, tail = os.path.split(__file__)
    file_path = os.path.join(base_path, 'mapfile_encoding.xml')
    wms = BaseWMSFactory() 
    wms.loadXML(file_path)
    wms.finalize()

    conf = SafeConfigParser()
    conf.readfp(open(os.path.join(base_path, 'ogcserver.conf')))

    wms111 = ServiceHandler111(conf, wms, "localhost")
    wms130 = ServiceHandler130(conf, wms, "localhost")

    return (conf, {
        '1.1.1': wms111.GetCapabilities({}),
        '1.3.0': wms130.GetCapabilities({})
    })

def test_encoding():
    conf, caps = _wms_capabilities()

    # Check the response is encoded in UTF-8
    # Search for the title in the response
    if conf.get('service', 'title') not in caps['1.1.1'].content:
        raise Exception('GetCapabilities is not correctly encoded')

    return True
 
def test_latlonbbox():
    from lxml import etree as ElementTree

    def find_in_root_layer(xml_string, layer_path, tag):
        caps_dom = ElementTree.XML(xml_string)
        root_lyr = caps_dom.find(layer_path)
        if root_lyr is None:
            raise Exception('Hm, couldn\'t find a layer')
        if root_lyr.find(tag) is None:
            print ElementTree.tostring(root_lyr, pretty_print=True)
            raise Exception('Root layer is missing %s' % tag)

    conf, caps = _wms_capabilities()
    find_in_root_layer(caps['1.1.1'].content, 'Capability/Layer', 'LatLonBoundingBox')
    find_in_root_layer(caps['1.3.0'].content, 
        '{http://www.opengis.net/wms}Capability/{http://www.opengis.net/wms}Layer', 
        '{http://www.opengis.net/wms}EX_GeographicBoundingBox')

    return True
