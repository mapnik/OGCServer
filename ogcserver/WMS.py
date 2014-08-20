"""Interface for registering map styles and layers for availability in WMS Requests."""

import re
import sys
import ConfigParser
from mapnik import Style, Map, load_map, load_map_from_string, Envelope, Coord

from ogcserver import common
from ogcserver.wms111 import ServiceHandler as ServiceHandler111
from ogcserver.wms130 import ServiceHandler as ServiceHandler130
from ogcserver.exceptions import OGCException, ServerConfigurationError

def ServiceHandlerFactory(conf, mapfactory, onlineresource, version):

    if not version:
        version = common.Version()
    else:
        version = common.Version(version)
    if version >= '1.3.0':
        return ServiceHandler130(conf, mapfactory, onlineresource)
    else:
        return ServiceHandler111(conf, mapfactory, onlineresource)

def extract_named_rules(s_obj):
    s = Style()
    s.names = []
    if isinstance(s_obj,Style):
        for rule in s_obj.rules:
            if rule.name:
                s.rules.append(rule)
                if not rule.name in s.names:
                    s.names.append(rule.name)
    elif isinstance(s_obj,list):
        for sty in s_obj:
            for rule in sty.rules:
                if rule.name:
                    s.rules.append(rule)
                    if not rule.name in s.names:
                        s.names.append(rule.name)
    if len(s.rules):
        return s

class BaseWMSFactory:
    def __init__(self, configpath=None):
        self.layers = {}
        self.ordered_layers = []
        self.styles = {}
        self.aggregatestyles = {}
        self.map_attributes = {}
        self.meta_styles = {}
        self.meta_layers = {}
        self.configpath = configpath
        self.latlonbb = None

    def loadXML(self, xmlfile=None, strict=False, xmlstring='', basepath=''):
        config = ConfigParser.SafeConfigParser()
        map_wms_srs = None
        if self.configpath:
            config.readfp(open(self.configpath))

            if config.has_option('map', 'wms_srs'):
                map_wms_srs = config.get('map', 'wms_srs')

        tmp_map = Map(0,0)
        if xmlfile:
            load_map(tmp_map, xmlfile, strict)
        elif xmlstring:
            load_map_from_string(tmp_map, xmlstring, strict, basepath)
        else:
            raise ServerConfigurationError("Mapnik configuration XML is not specified - 'xmlfile' and 'xmlstring' variables are empty.\
Please set one of this variables to load mapnik map object.")
        # parse map level attributes
        if tmp_map.background:
            self.map_attributes['bgcolor'] = tmp_map.background
        if tmp_map.buffer_size:
            self.map_attributes['buffer_size'] = tmp_map.buffer_size
        for lyr in tmp_map.layers:
            layer_section = 'layer_%s' % lyr.name
            layer_wms_srs = None
            if config.has_option(layer_section, 'wms_srs'):
                layer_wms_srs = config.get(layer_section, 'wms_srs')
            else:
                layer_wms_srs = map_wms_srs

            if config.has_option(layer_section, 'title'):
                lyr.title = config.get(layer_section, 'title')
            else:
                lyr.title = ''

            if config.has_option(layer_section, 'abstract'):
                lyr.abstract = config.get(layer_section, 'abstract')
            else:
                lyr.abstract = ''

            style_count = len(lyr.styles)
            if style_count == 0:
                raise ServerConfigurationError("Cannot register Layer '%s' without a style" % lyr.name)
            elif style_count == 1:
                style_obj = tmp_map.find_style(lyr.styles[0])
                style_name = lyr.styles[0]

                meta_s = extract_named_rules(style_obj)
                if meta_s:
                    self.meta_styles['%s_meta' % lyr.name] = meta_s
                    if hasattr(lyr,'abstract'):
                        name_ = lyr.abstract
                    else:
                        name_ = lyr.name
                    meta_layer_name = '%s:%s' % (name_,'-'.join(meta_s.names))
                    meta_layer_name = meta_layer_name.replace(' ','_')
                    self.meta_styles[meta_layer_name] = meta_s
                    meta_lyr = common.copy_layer(lyr)
                    meta_lyr.meta_style = meta_layer_name
                    meta_lyr.name = meta_layer_name
                    meta_lyr.wmsextrastyles = ()
                    meta_lyr.defaultstyle = meta_layer_name
                    meta_lyr.wms_srs = layer_wms_srs
                    self.ordered_layers.append(meta_lyr)
                    self.meta_layers[meta_layer_name] = meta_lyr
                    print meta_layer_name

                if style_name not in self.aggregatestyles.keys() and style_name not in self.styles.keys():
                    self.register_style(style_name, style_obj)

                # must copy layer here otherwise we'll segfault
                lyr_ = common.copy_layer(lyr)
                lyr_.wms_srs = layer_wms_srs
                self.register_layer(lyr_, style_name, extrastyles=(style_name,))

            elif style_count > 1:
                for style_name in lyr.styles:
                    style_obj = tmp_map.find_style(style_name)

                    meta_s = extract_named_rules(style_obj)
                    if meta_s:
                        self.meta_styles['%s_meta' % lyr.name] = meta_s
                        if hasattr(lyr,'abstract'):
                            name_ = lyr.abstract
                        else:
                            name_ = lyr.name
                        meta_layer_name = '%s:%s' % (name_,'-'.join(meta_s.names))
                        meta_layer_name = meta_layer_name.replace(' ','_')
                        self.meta_styles[meta_layer_name] = meta_s
                        meta_lyr = common.copy_layer(lyr)
                        meta_lyr.meta_style = meta_layer_name
                        print meta_layer_name
                        meta_lyr.name = meta_layer_name
                        meta_lyr.wmsextrastyles = ()
                        meta_lyr.defaultstyle = meta_layer_name
                        meta_lyr.wms_srs = layer_wms_srs
                        self.ordered_layers.append(meta_lyr)
                        self.meta_layers[meta_layer_name] = meta_lyr

                    if style_name not in self.aggregatestyles.keys() and style_name not in self.styles.keys():
                        self.register_style(style_name, style_obj)
                aggregates = tuple([sty for sty in lyr.styles])
                aggregates_name = '%s_aggregates' % lyr.name
                self.register_aggregate_style(aggregates_name,aggregates)
                # must copy layer here otherwise we'll segfault
                lyr_ = common.copy_layer(lyr)
                lyr_.wms_srs = layer_wms_srs
                self.register_layer(lyr_, aggregates_name, extrastyles=aggregates)
                if 'default' in aggregates:
                    sys.stderr.write("Warning: Multi-style layer '%s' contains a regular style named 'default'. \
This style will effectively be hidden by the 'all styles' default style for multi-style layers.\n" % lyr_.name)

    def register_layer(self, layer, defaultstyle, extrastyles=()):
        layername = layer.name
        if not layername:
            raise ServerConfigurationError('Attempted to register an unnamed layer.')
        if not layer.wms_srs and not re.match('^\+init=epsg:\d+$', layer.srs) and not re.match('^\+proj=.*$', layer.srs):
            raise ServerConfigurationError('Attempted to register a layer without an epsg projection defined.')
        if defaultstyle not in self.styles.keys() + self.aggregatestyles.keys():
            raise ServerConfigurationError('Attempted to register a layer with an non-existent default style.')
        layer.wmsdefaultstyle = defaultstyle
        if isinstance(extrastyles, tuple):
            for stylename in extrastyles:
                if type(stylename) == type(''):
                    if stylename not in self.styles.keys() + self.aggregatestyles.keys():
                        raise ServerConfigurationError('Attempted to register a layer with an non-existent extra style.')
                else:
                    ServerConfigurationError('Attempted to register a layer with an invalid extra style name.')
            layer.wmsextrastyles = extrastyles
        else:
            raise ServerConfigurationError('Layer "%s" was passed an invalid list of extra styles.  List must be a tuple of strings.' % layername)
        layerproj = common.Projection(layer.srs)
        env = layer.envelope()
        llp = layerproj.inverse(Coord(env.minx, env.miny))
        urp = layerproj.inverse(Coord(env.maxx, env.maxy))
        if self.latlonbb is None:
            self.latlonbb = Envelope(llp, urp)
        else:
            self.latlonbb.expand_to_include(Envelope(llp, urp))
        self.ordered_layers.append(layer)
        self.layers[layername] = layer

    def register_style(self, name, style):
        if not name:
            raise ServerConfigurationError('Attempted to register a style without providing a name.')
        if name in self.aggregatestyles.keys() or name in self.styles.keys():
            raise ServerConfigurationError("Attempted to register a style with a name already in use: '%s'" % name)
        if not isinstance(style, Style):
            raise ServerConfigurationError('Bad style object passed to register_style() for style "%s".' % name)
        self.styles[name] = style

    def register_aggregate_style(self, name, stylenames):
        if not name:
            raise ServerConfigurationError('Attempted to register an aggregate style without providing a name.')
        if name in self.aggregatestyles.keys() or name in self.styles.keys():
            raise ServerConfigurationError('Attempted to register an aggregate style with a name already in use.')
        self.aggregatestyles[name] = []
        for stylename in stylenames:
            if stylename not in self.styles.keys():
                raise ServerConfigurationError('Attempted to register an aggregate style containing a style that does not exist.')
            self.aggregatestyles[name].append(stylename)

    def finalize(self):
        if len(self.layers) == 0:
            raise ServerConfigurationError('No layers defined!')
        if len(self.styles) == 0:
            raise ServerConfigurationError('No styles defined!')
        for layer in self.layers.values():
            for style in list(layer.styles) + list(layer.wmsextrastyles):
                if style not in self.styles.keys() + self.aggregatestyles.keys():
                    raise ServerConfigurationError('Layer "%s" refers to undefined style "%s".' % (layer.name, style))
