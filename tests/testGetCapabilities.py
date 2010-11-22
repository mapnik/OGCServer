import nose

def test_encoding():
    import os
    from ogcserver.configparser import SafeConfigParser
    from ogcserver.WMS import BaseWMSFactory
    from ogcserver.wms111 import ServiceHandler as ServiceHandler111
    from ogcserver.wms130 import ServiceHandler as ServiceHandler130

    base_path, tail = os.path.split(__file__)
    file_path = os.path.join(base_path, 'mapfile_encoding.xml')
    wms = BaseWMSFactory() 
    wms.loadXML(file_path)
    wms.finalize()

    conf = SafeConfigParser()
    conf.readfp(open(os.path.join(base_path, 'ogcserver.conf')))

    wms111 = ServiceHandler111(conf, wms, "localhost")
    wms111.GetCapabilities({})
    
    wms130 = ServiceHandler130(conf, wms, "localhost")
    wms130.GetCapabilities({})

    return True
 
