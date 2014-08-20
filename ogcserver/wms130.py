"""WMS 1.3.0 compliant GetCapabilities, GetMap, GetFeatureInfo, and Exceptions interface."""

from mapnik import Coord

from xml.etree import ElementTree
ElementTree.register_namespace('', "http://www.opengis.net/wms")
ElementTree.register_namespace('xlink', "http://www.w3.org/1999/xlink")

from ogcserver.common import ParameterDefinition, Response, Version, ListFactory, \
                   ColorFactory, CRSFactory, CRS, WMSBaseServiceHandler, \
                   BaseExceptionHandler, Projection, Envelope, to_unicode
from ogcserver.exceptions import OGCException, ServerConfigurationError

class ServiceHandler(WMSBaseServiceHandler):

    SERVICE_PARAMS = {
        'GetCapabilities': {
            'format': ParameterDefinition(False, str, 'text/xml', ('text/xml',)),
            'updatesequence': ParameterDefinition(False, str)
        },
        'GetMap': {
            'layers': ParameterDefinition(True, ListFactory(str)),
            'styles': ParameterDefinition(True, ListFactory(str)),
            'crs': ParameterDefinition(True, CRSFactory(['EPSG'])),
            'bbox': ParameterDefinition(True, ListFactory(float)),
            'width': ParameterDefinition(True, int),
            'height': ParameterDefinition(True, int),
            'format': ParameterDefinition(True, str, allowedvalues=('image/png','image/png8', 'image/jpeg')),
            'transparent': ParameterDefinition(False, str, 'FALSE', ('TRUE', 'FALSE','true','True','false','False')),
            'bgcolor': ParameterDefinition(False, ColorFactory, None),
            'exceptions': ParameterDefinition(False, str, 'XML', ('XML', 'INIMAGE', 'BLANK','HTML'),True),
        },
        'GetFeatureInfo': {
            'layers': ParameterDefinition(True, ListFactory(str)),
            'styles': ParameterDefinition(False, ListFactory(str)),
            'crs': ParameterDefinition(True, CRSFactory(['EPSG'])),
            'bbox': ParameterDefinition(True, ListFactory(float)),
            'width': ParameterDefinition(True, int),
            'height': ParameterDefinition(True, int),
            'format': ParameterDefinition(False, str, allowedvalues=('image/png', 'image/jpeg')),
            'transparent': ParameterDefinition(False, str, 'FALSE', ('TRUE', 'FALSE','true','True','false','False')),
            'bgcolor': ParameterDefinition(False, ColorFactory, ColorFactory('0xFFFFFF')),
            'exceptions': ParameterDefinition(False, str, 'XML', ('XML', 'INIMAGE', 'BLANK','HTML'),True),
            'query_layers': ParameterDefinition(True, ListFactory(str)),
            'info_format': ParameterDefinition(True, str, allowedvalues=('text/plain', 'text/xml')),
            'feature_count': ParameterDefinition(False, int, 1),
            'i': ParameterDefinition(False, float),
            'j': ParameterDefinition(False, float),
            'y': ParameterDefinition(False, float),
            'x': ParameterDefinition(False, float)
        }
    }

    CONF_SERVICE = [
        ['title', 'Title', str],
        ['abstract', 'Abstract', str],
        ['onlineresource', 'OnlineResource', str],
        ['fees', 'Fees', str],
        ['accessconstraints', 'AccessConstraints', str],
        ['layerlimit', 'LayerLimit', int],
        ['maxwidth', 'MaxWidth', int],
        ['maxheight', 'MaxHeight', int],
        ['keywordlist', 'KeywordList', str]
    ]

    capabilitiesxmltemplate = """<?xml version="1.0" encoding="UTF-8"?>
    <WMS_Capabilities version="1.3.0" xmlns="http://www.opengis.net/wms"
                                      xmlns:xlink="http://www.w3.org/1999/xlink"
                                      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                                      xsi:schemaLocation="http://www.opengis.net/wms http://schemas.opengis.net/wms/1.3.0/capabilities_1_3_0.xsd">
      <Service>
        <Name>WMS</Name>
      </Service>
      <Capability>
        <Request>
          <GetCapabilities>
            <Format>text/xml</Format>
            <DCPType>
              <HTTP>
                <Get>
                  <OnlineResource xlink:type="simple"/>
                </Get>
              </HTTP>
            </DCPType>
          </GetCapabilities>
          <GetMap>
            <Format>image/png</Format>
            <Format>image/png8</Format>
            <Format>image/jpeg</Format>
            <DCPType>
              <HTTP>
                <Get>
                  <OnlineResource xlink:type="simple"/>
                </Get>
              </HTTP>
            </DCPType>
          </GetMap>
          <GetFeatureInfo>
            <Format>text/plain</Format>
            <DCPType>
              <HTTP>
                <Get>
                  <OnlineResource xlink:type="simple"/>
                </Get>
              </HTTP>
            </DCPType>
          </GetFeatureInfo>
        </Request>
        <Exception>
          <Format>XML</Format>
          <Format>INIMAGE</Format>
          <Format>BLANK</Format>
          <Format>HTML</Format>
        </Exception>
        <Layer>
        </Layer>
      </Capability>
    </WMS_Capabilities>
    """

    def __init__(self, conf, mapfactory, opsonlineresource):
        self.conf = conf
        self.mapfactory = mapfactory
        self.opsonlineresource = opsonlineresource
        if self.conf.has_option('service', 'allowedepsgcodes'):
            self.allowedepsgcodes = map(lambda code: 'epsg:%s' % code, self.conf.get('service', 'allowedepsgcodes').split(','))
        else:
            raise ServerConfigurationError('Allowed EPSG codes not properly configured.')
        self.capabilities = None

    def GetCapabilities(self, params):
        if not self.capabilities:
            capetree = ElementTree.fromstring(self.capabilitiesxmltemplate)

            elements = capetree.findall('{http://www.opengis.net/wms}Capability//{http://www.opengis.net/wms}OnlineResource')
            for element in elements:
                element.set('xlink:href', self.opsonlineresource)

            self.processServiceCapabilities(capetree)

            rootlayerelem = capetree.find('{http://www.opengis.net/wms}Capability/{http://www.opengis.net/wms}Layer')

            rootlayername = ElementTree.Element('{http://www.opengis.net/wms}Name')
            if self.conf.has_option('map', 'wms_name'):
                rootlayername.text = to_unicode(self.conf.get('map', 'wms_name'))
            else:
                rootlayername.text = '__all__'
            rootlayerelem.append(rootlayername)

            rootlayertitle = ElementTree.Element('{http://www.opengis.net/wms}Title')
            if self.conf.has_option('map', 'wms_title'):
                rootlayertitle.text = to_unicode(self.conf.get('map', 'wms_title'))
            else:
                rootlayertitle.text = 'OGCServer WMS Server'
            rootlayerelem.append(rootlayertitle)

            rootlayerabstract = ElementTree.Element('{http://www.opengis.net/wms}Abstract')
            if self.conf.has_option('map', 'wms_abstract'):
                rootlayerabstract.text = to_unicode(self.conf.get('map', 'wms_abstract'))
            else:
                rootlayerabstract.text = 'OGCServer WMS Server'
            rootlayerelem.append(rootlayerabstract)

            layerexgbb = ElementTree.Element('{http://www.opengis.net/wms}EX_GeographicBoundingBox')
            exgbb_wbl = ElementTree.Element('{http://www.opengis.net/wms}westBoundLongitude')
            exgbb_wbl.text = str(self.mapfactory.latlonbb.minx)
            layerexgbb.append(exgbb_wbl)
            exgbb_ebl = ElementTree.Element('{http://www.opengis.net/wms}eastBoundLongitude')
            exgbb_ebl.text = str(self.mapfactory.latlonbb.maxx)
            layerexgbb.append(exgbb_ebl)
            exgbb_sbl = ElementTree.Element('{http://www.opengis.net/wms}southBoundLatitude')
            exgbb_sbl.text = str(self.mapfactory.latlonbb.miny)
            layerexgbb.append(exgbb_sbl)
            exgbb_nbl = ElementTree.Element('{http://www.opengis.net/wms}northBoundLatitude')
            exgbb_nbl.text = str(self.mapfactory.latlonbb.maxy)
            layerexgbb.append(exgbb_nbl)
            rootlayerelem.append(layerexgbb)

            for epsgcode in self.allowedepsgcodes:
                rootlayercrs = ElementTree.Element('{http://www.opengis.net/wms}CRS')
                rootlayercrs.text = epsgcode.upper()
                rootlayerelem.append(rootlayercrs)

            for layer in self.mapfactory.ordered_layers:
                layerproj = Projection(layer.srs)
                layername = ElementTree.Element('{http://www.opengis.net/wms}Name')
                layername.text = to_unicode(layer.name)
                env = layer.envelope()
                layerexgbb = ElementTree.Element('{http://www.opengis.net/wms}EX_GeographicBoundingBox')
                ll = layerproj.inverse(Coord(env.minx, env.miny))
                ur = layerproj.inverse(Coord(env.maxx, env.maxy))
                exgbb_wbl = ElementTree.Element('{http://www.opengis.net/wms}westBoundLongitude')
                exgbb_wbl.text = str(ll.x)
                layerexgbb.append(exgbb_wbl)
                exgbb_ebl = ElementTree.Element('{http://www.opengis.net/wms}eastBoundLongitude')
                exgbb_ebl.text = str(ur.x)
                layerexgbb.append(exgbb_ebl)
                exgbb_sbl = ElementTree.Element('{http://www.opengis.net/wms}southBoundLatitude')
                exgbb_sbl.text = str(ll.y)
                layerexgbb.append(exgbb_sbl)
                exgbb_nbl = ElementTree.Element('{http://www.opengis.net/wms}northBoundLatitude')
                exgbb_nbl.text = str(ur.y)
                layerexgbb.append(exgbb_nbl)
                layerbbox = ElementTree.Element('{http://www.opengis.net/wms}BoundingBox')
                if layer.wms_srs:
                    layerbbox.set('CRS', layer.wms_srs)
                else:
                    layerbbox.set('CRS', layerproj.epsgstring())
                layerbbox.set('minx', str(env.minx))
                layerbbox.set('miny', str(env.miny))
                layerbbox.set('maxx', str(env.maxx))
                layerbbox.set('maxy', str(env.maxy))
                layere = ElementTree.Element('{http://www.opengis.net/wms}Layer')
                layere.append(layername)
                layertitle = ElementTree.Element('{http://www.opengis.net/wms}Title')
                if hasattr(layer,'title'):
                    layertitle.text = to_unicode(layer.title)
                    if layertitle.text == '':
                        layertitle.text = to_unicode(layer.name)
                else:
                    layertitle.text = to_unicode(layer.name)
                layere.append(layertitle)
                layerabstract = ElementTree.Element('{http://www.opengis.net/wms}Abstract')
                if hasattr(layer,'abstract'):
                    layerabstract.text = to_unicode(layer.abstract)
                else:
                    layerabstract.text = 'no abstract'
                layere.append(layerabstract)
                if layer.queryable:
                    layere.set('queryable', '1')
                layere.append(layerexgbb)
                layere.append(layerbbox)
                style_count = len(layer.wmsextrastyles)
                if style_count > 0:
                    extrastyles = layer.wmsextrastyles
                    if style_count > 1:
                        extrastyles = ['default'] + [x for x in extrastyles if x != 'default']
                    for extrastyle in extrastyles:
                        style = ElementTree.Element('{http://www.opengis.net/wms}Style')
                        stylename = ElementTree.Element('{http://www.opengis.net/wms}Name')
                        stylename.text = to_unicode(extrastyle)
                        styletitle = ElementTree.Element('{http://www.opengis.net/wms}Title')
                        styletitle.text = to_unicode(extrastyle)
                        style.append(stylename)
                        style.append(styletitle)
                        if style_count > 1 and extrastyle == 'default':
                            styleabstract = ElementTree.Element('{http://www.opengis.net/wms}Abstract')
                            styleabstract.text = to_unicode('This layer\'s default style that combines all its other named styles.')
                            style.append(styleabstract)
                        layere.append(style)
                rootlayerelem.append(layere)
            self.capabilities = ElementTree.tostring(capetree,encoding='UTF-8')
        response = Response('text/xml', self.capabilities)
        return response

    def GetMap(self, params):
        if params['width'] > int(self.conf.get('service', 'maxwidth')) or params['height'] > int(self.conf.get('service', 'maxheight')):
            raise OGCException('Requested map size exceeds limits set by this server.')
        return WMSBaseServiceHandler.GetMap(self, params)

    def GetFeatureInfo(self, params):
        # support for QGIS 1.3.0 GetFeatInfo...
        if not params.get('i') and not params.get('j'):
            params['i'] = params.get('x',params.get('X'))
            params['j'] = params.get('y',params.get('Y'))
        # support 1.1.1 request that end up using 1.3.0 impl
        # because the version is not included in GetMap
        # ArcGIS 9.2 for example makes 1.1.1 GetCaps request
        # but leaves version out of GetMap
        if not params.get('crs') and params.get('srs'):
            params['crs'] = params.get('srs')
        return WMSBaseServiceHandler.GetFeatureInfo(self, params, 'query_map_point')

    def _buildMap(self, params):
        """ Override _buildMap method to handle reverse axis ordering in WMS 1.3.0.

        More info: http://mapserver.org/development/rfc/ms-rfc-30.html
        http://trac.osgeo.org/mapserver/changeset/10459

        'when using epsg code >=4000 and <5000 will be assumed to have a reversed axes.'

        """
        # Call superclass method
        m = WMSBaseServiceHandler._buildMap(self, params)
        # for range of epsg codes reverse axis as per 1.3.0 spec
        if params['crs'].code >= 4000 and params['crs'].code < 5000:
            bbox = params['bbox']
            # MapInfo Pro 10 does not "know" this is the way and gets messed up
            if not 'mapinfo' in params['HTTP_USER_AGENT'].lower():
                m.zoom_to_box(Envelope(bbox[1], bbox[0], bbox[3], bbox[2]))
        return m

class ExceptionHandler(BaseExceptionHandler):

    xmlmimetype = "text/xml"

    xmltemplate = ElementTree.fromstring("""<?xml version='1.0' encoding="UTF-8"?>
    <ServiceExceptionReport version="1.3.0"
                            xmlns="http://www.opengis.net/ogc"
                            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                            xsi:schemaLocation="http://www.opengis.net/ogc http://schemas.opengis.net/wms/1.3.0/exceptions_1_3_0.xsd">
      <ServiceException/>
    </ServiceExceptionReport>
    """)

    xpath = '{http://www.opengis.net/ogc}ServiceException'

    handlers = {'XML': BaseExceptionHandler.xmlhandler,
                'INIMAGE': BaseExceptionHandler.inimagehandler,
                'BLANK': BaseExceptionHandler.blankhandler,
                'HTML': BaseExceptionHandler.htmlhandler}

    defaulthandler = 'XML'

