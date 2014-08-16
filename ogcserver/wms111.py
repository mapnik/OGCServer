"""WMS 1.1.1 compliant GetCapabilities, GetMap, GetFeatureInfo, and Exceptions interface."""

from mapnik import Coord

from xml.etree import ElementTree
ElementTree.register_namespace('', "http://www.opengis.net/wms")
ElementTree.register_namespace('xlink', "http://www.w3.org/1999/xlink")

from ogcserver.common import ParameterDefinition, Response, Version, ListFactory, \
                   ColorFactory, CRSFactory, WMSBaseServiceHandler, CRS, \
                   BaseExceptionHandler, Projection, to_unicode
from ogcserver.exceptions import OGCException, ServerConfigurationError


class ServiceHandler(WMSBaseServiceHandler):

    SERVICE_PARAMS = {
        'GetCapabilities': {
            'updatesequence': ParameterDefinition(False, str)
        },
        'GetMap': {
            'layers': ParameterDefinition(True, ListFactory(str)),
            'styles': ParameterDefinition(True, ListFactory(str)),
            'srs': ParameterDefinition(True, CRSFactory(['EPSG'])),
            'bbox': ParameterDefinition(True, ListFactory(float)),
            'width': ParameterDefinition(True, int),
            'height': ParameterDefinition(True, int),
            'format': ParameterDefinition(True, str, allowedvalues=('image/png','image/png8', 'image/jpeg')),
            'transparent': ParameterDefinition(False, str, 'FALSE', ('TRUE', 'FALSE','true','True','false','False')),
            'bgcolor': ParameterDefinition(False, ColorFactory, None),
            'exceptions': ParameterDefinition(False, str, 'application/vnd.ogc.se_xml', ('application/vnd.ogc.se_xml', 'application/vnd.ogc.se_inimage', 'application/vnd.ogc.se_blank','text/html'),True)
        },
        'GetFeatureInfo': {
            'layers': ParameterDefinition(True, ListFactory(str)),
            'styles': ParameterDefinition(False, ListFactory(str)),
            'srs': ParameterDefinition(True, CRSFactory(['EPSG'])),
            'bbox': ParameterDefinition(True, ListFactory(float)),
            'width': ParameterDefinition(True, int),
            'height': ParameterDefinition(True, int),
            'format': ParameterDefinition(False, str, allowedvalues=('image/png', 'image/jpeg')),
            'transparent': ParameterDefinition(False, str, 'FALSE', ('TRUE', 'FALSE','true','True','false','False')),
            'bgcolor': ParameterDefinition(False, ColorFactory, ColorFactory('0xFFFFFF')),
            'exceptions': ParameterDefinition(False, str, 'application/vnd.ogc.se_xml', ('application/vnd.ogc.se_xml', 'application/vnd.ogc.se_inimage', 'application/vnd.ogc.se_blank','text/html'),True),
            'query_layers': ParameterDefinition(True, ListFactory(str)),
            'info_format': ParameterDefinition(True, str, allowedvalues=('text/plain', 'text/xml')),
            'feature_count': ParameterDefinition(False, int, 1),
            'x': ParameterDefinition(True, int),
            'y': ParameterDefinition(True, int)
        }
    }

    CONF_SERVICE = [
        ['title', 'Title', str],
        ['abstract', 'Abstract', str],
        ['onlineresource', 'OnlineResource', str],
        ['fees', 'Fees', str],
        ['accessconstraints', 'AccessConstraints', str],
        ['keywordlist', 'KeywordList', str]
    ]

    capabilitiesxmltemplate = """
    <!DOCTYPE WMT_MS_Capabilities SYSTEM "http://schemas.opengis.net/wms/1.1.1/WMS_MS_Capabilities.dtd">
    <WMT_MS_Capabilities version="1.1.1" updateSequence="0" xmlns:xlink="http://www.w3.org/1999/xlink">
      <Service>
        <Name>OGC:WMS</Name>
      </Service>
      <Capability>
        <Request>
          <GetCapabilities>
            <Format>application/vnd.ogc.wms_xml</Format>
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
                  <OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink" xlink:type="simple"/>
                </Get>
              </HTTP>
            </DCPType>
          </GetMap>
          <GetFeatureInfo>
            <Format>text/plain</Format>
            <DCPType>
              <HTTP>
                <Get>
                  <OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink" xlink:type="simple"/>
                </Get>
              </HTTP>
            </DCPType>
          </GetFeatureInfo>
        </Request>
        <Exception>
          <Format>application/vnd.ogc.se_xml</Format>
          <Format>application/vnd.ogc.se_inimage</Format>
          <Format>application/vnd.ogc.se_blank</Format>
          <Format>text/html</Format>
        </Exception>
        <Layer>
        </Layer>
      </Capability>
    </WMT_MS_Capabilities>
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

            elements = capetree.findall('Capability//OnlineResource')
            for element in elements:
                element.set('xlink:href', self.opsonlineresource)

            self.processServiceCapabilities(capetree)

            rootlayerelem = capetree.find('Capability/Layer')

            rootlayername = ElementTree.Element('Name')
            if self.conf.has_option('map', 'wms_name'):
                rootlayername.text = to_unicode(self.conf.get('map', 'wms_name'))
            else:
                rootlayername.text = '__all__'
            rootlayerelem.append(rootlayername)

            rootlayertitle = ElementTree.Element('Title')
            if self.conf.has_option('map', 'wms_title'):
                rootlayertitle.text = to_unicode(self.conf.get('map', 'wms_title'))
            else:
                rootlayertitle.text = 'OGCServer WMS Server'
            rootlayerelem.append(rootlayertitle)

            rootlayerabstract = ElementTree.Element('Abstract')
            if self.conf.has_option('map', 'wms_abstract'):
                rootlayerabstract.text = to_unicode(self.conf.get('map', 'wms_abstract'))
            else:
                rootlayerabstract.text = 'OGCServer WMS Server'
            rootlayerelem.append(rootlayerabstract)

            latlonbb = ElementTree.Element('LatLonBoundingBox')
            latlonbb.set('minx', str(self.mapfactory.latlonbb.minx))
            latlonbb.set('miny', str(self.mapfactory.latlonbb.miny))
            latlonbb.set('maxx', str(self.mapfactory.latlonbb.maxx))
            latlonbb.set('maxy', str(self.mapfactory.latlonbb.maxy))
            rootlayerelem.append(latlonbb)

            for epsgcode in self.allowedepsgcodes:
                rootlayercrs = ElementTree.Element('SRS')
                rootlayercrs.text = epsgcode.upper()
                rootlayerelem.append(rootlayercrs)

            for layer in self.mapfactory.ordered_layers:
                layerproj = Projection(layer.srs)
                layername = ElementTree.Element('Name')
                layername.text = to_unicode(layer.name)
                env = layer.envelope()
                llp = layerproj.inverse(Coord(env.minx, env.miny))
                urp = layerproj.inverse(Coord(env.maxx, env.maxy))
                latlonbb = ElementTree.Element('LatLonBoundingBox')
                latlonbb.set('minx', str(llp.x))
                latlonbb.set('miny', str(llp.y))
                latlonbb.set('maxx', str(urp.x))
                latlonbb.set('maxy', str(urp.y))
                layerbbox = ElementTree.Element('BoundingBox')
                if layer.wms_srs:
                    layerbbox.set('SRS', layer.wms_srs)
                else:
                    layerbbox.set('SRS', layerproj.epsgstring())
                layerbbox.set('minx', str(env.minx))
                layerbbox.set('miny', str(env.miny))
                layerbbox.set('maxx', str(env.maxx))
                layerbbox.set('maxy', str(env.maxy))
                layere = ElementTree.Element('Layer')
                layere.append(layername)
                layertitle = ElementTree.Element('Title')
                if hasattr(layer,'title'):
                    layertitle.text = to_unicode(layer.title)
                    if layertitle.text == '':
                        layertitle.text = to_unicode(layer.name)
                else:
                    layertitle.text = to_unicode(layer.name)
                layere.append(layertitle)
                layerabstract = ElementTree.Element('Abstract')
                if hasattr(layer,'abstract'):
                    layerabstract.text = to_unicode(layer.abstract)
                else:
                    layerabstract.text = 'no abstract'
                layere.append(layerabstract)
                if layer.queryable:
                    layere.set('queryable', '1')
                layere.append(latlonbb)
                layere.append(layerbbox)
                style_count = len(layer.wmsextrastyles)
                if style_count > 0:
                    extrastyles = layer.wmsextrastyles
                    if style_count > 1:
                        extrastyles = ['default'] + [x for x in extrastyles if x != 'default']
                    for extrastyle in extrastyles:
                        style = ElementTree.Element('Style')
                        stylename = ElementTree.Element('Name')
                        stylename.text = to_unicode(extrastyle)
                        styletitle = ElementTree.Element('Title')
                        styletitle.text = to_unicode(extrastyle)
                        style.append(stylename)
                        style.append(styletitle)
                        if style_count > 1 and extrastyle == 'default':
                            styleabstract = ElementTree.Element('Abstract')
                            styleabstract.text = to_unicode('This layer\'s default style that combines all its other named styles.')
                            style.append(styleabstract)
                        layere.append(style)
                rootlayerelem.append(layere)
            self.capabilities = ElementTree.tostring(capetree,encoding='UTF-8')
        response = Response('application/vnd.ogc.wms_xml', self.capabilities)
        return response

    def GetMap(self, params):
        params['crs'] = params['srs']
        return WMSBaseServiceHandler.GetMap(self, params)

    def GetFeatureInfo(self, params):
        params['crs'] = params['srs']
        params['i'] = params['x']
        params['j'] = params['y']
        return WMSBaseServiceHandler.GetFeatureInfo(self, params, 'query_map_point')

class ExceptionHandler(BaseExceptionHandler):

    xmlmimetype = "application/vnd.ogc.se_xml"

    xmltemplate = ElementTree.fromstring("""<?xml version='1.0' encoding="UTF-8" standalone="no"?>
    <!DOCTYPE ServiceExceptionReport SYSTEM "http://www.digitalearth.gov/wmt/xml/exception_1_1_1.dtd">
    <ServiceExceptionReport version="1.1.1">
      <ServiceException />
    </ServiceExceptionReport>
    """)

    xpath = 'ServiceException'

    handlers = {'application/vnd.ogc.se_xml': BaseExceptionHandler.xmlhandler,
                'application/vnd.ogc.se_inimage': BaseExceptionHandler.inimagehandler,
                'application/vnd.ogc.se_blank': BaseExceptionHandler.blankhandler,
                'text/html': BaseExceptionHandler.htmlhandler}

    defaulthandler = 'application/vnd.ogc.se_xml'
