import nose
import os
from ogcserver.WMS import BaseWMSFactory

def test_wms_capabilities():
    base_path, tail = os.path.split(__file__)
    file_path = os.path.join(base_path, 'mapfile_encoding.xml')
    wms = BaseWMSFactory()
    with open(file_path) as f:
        settings = f.read()
    wms.loadXML(xmlstring=settings, basepath=base_path)
    wms.finalize()
    
    if len(wms.layers) != 1:
        raise Exception('Incorrect number of layers')
    if len(wms.styles) != 1:
        raise Exception('Incorrect number of styles')
    
    return True
