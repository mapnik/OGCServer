import os
from ogcserver.WMS import BaseWMSFactory
from mapnik import Style, Layer, Map, load_map

class WMSFactory(BaseWMSFactory):
    def __init__(self):
        BaseWMSFactory.__init__(self)
        base_path, tail = os.path.split(__file__)
        file_path = os.path.join(base_path, 'mapfile_encoding.xml') 
        self.loadXML(file_path)
        self.finalize()
