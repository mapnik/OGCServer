import nose

def test_encoding():
    import os
    from ogcserver.configparser import SafeConfigParser
    from ogcserver.WMS import BaseWMSFactory
    from ogcserver.wms111 import ServiceHandler as ServiceHandler111
    from ogcserver.wms130 import ServiceHandler as ServiceHandler130

    base_path, tail = os.path.split(__file__)
    file_path = os.path.join(base_path, 'shape_encoding.xml')
    wms = BaseWMSFactory() 
    wms.loadXML(file_path)
    wms.finalize()

    conf = SafeConfigParser()
    conf.readfp(open(os.path.join(base_path, 'ogcserver.conf')))

# srs = EPSG:4326
# 3.00 , 42,35 - 3.15 , 42.51
# x = 5 , y = 6
    params = {}
    params['srs'] = 'epsg:4326'
    params['x'] = 5
    params['y'] = 5
    params['bbox'] = [3.00,42.35,3.15,42.51]
    params['height'] = 10
    params['width'] = 10
    params['layers'] = ['row']
    params['styles'] = ''
    params['info_format'] = 'text/plain'
    params['query_layers'] = ['row']
    wms111 = ServiceHandler111(conf, wms, "localhost")
    result = wms111.GetFeatureInfo(params)
    
    wms130 = ServiceHandler130(conf, wms, "localhost")
    wms130.GetCapabilities({})

    return True
 
