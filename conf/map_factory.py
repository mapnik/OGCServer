import os
from ogcserver.WMS import BaseWMSFactory
from mapnik import Style, Layer, Map, load_map

class WMSFactory(BaseWMSFactory):
    def __init__(self):
        import sys
        base_path, tail = os.path.split(__file__)
        configpath = os.path.join(base_path, 'ogcserver.conf')
        file_path = os.path.join(base_path, 'mapfile.xml') 
        BaseWMSFactory.__init__(self, configpath=configpath)
        self.loadXML(file_path)
        self.finalize()
