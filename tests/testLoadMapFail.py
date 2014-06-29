import nose
import os
from ogcserver.WMS import BaseWMSFactory
from ogcserver.exceptions import ServerConfigurationError

def test_wms_capabilities():
    wms = BaseWMSFactory()
    nose.tools.assert_raises(ServerConfigurationError, wms.loadXML)
    
    return True
