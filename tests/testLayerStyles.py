import nose
import os, sys
import StringIO
from ogcserver.configparser import SafeConfigParser
from ogcserver.WMS import BaseWMSFactory
from ogcserver.wms111 import ServiceHandler as ServiceHandler111
from ogcserver.wms130 import ServiceHandler as ServiceHandler130
from ogcserver.exceptions import OGCException

multi_style_err_text = 'Warning: Multi-style layer \'awkward-layer\' contains a regular \
style named \'default\'. This style will effectively be hidden by the \'all styles\' \
default style for multi-style layers.'

def _wms_services(mapfile):
    base_path, tail = os.path.split(__file__)
    file_path = os.path.join(base_path, mapfile)
    wms = BaseWMSFactory()

    # Layer 'awkward-layer' contains a regular style named 'default', which will
    # be hidden by OGCServer's auto-generated 'default' style. A warning message
    # is written to sys.stderr in loadXML.
    # Since we don't want to see this several times while unit testing (nose only
    # redirects sys.stdout), we redirect sys.stderr here into a StringIO buffer
    # temporarily.
    # As a side effect, we can as well search for the warning message and fail the
    # test, if it occurs zero or more than one times per loadXML invocation. However,
    # this test highly depends on the warning message text.
    stderr = sys.stderr
    errbuf = StringIO.StringIO()
    sys.stderr = errbuf

    wms.loadXML(file_path)

    sys.stderr = stderr
    errbuf.seek(0)
    warnings = 0
    for line in errbuf:
        if line.strip('\r\n') == multi_style_err_text:
            warnings += 1
        else:
            sys.stderr.write(line)
    errbuf.close()

    if warnings == 0:
        raise Exception('Expected warning message for layer \'awkward-layer\' not found in stderr stream.')
    elif warnings > 1:
        raise Exception('Expected warning message for layer \'awkward-layer\' occurred several times (%d) in stderr stream.' % warnings)

    wms.finalize()    

    conf = SafeConfigParser()
    conf.readfp(open(os.path.join(base_path, 'ogcserver.conf')))

    wms111 = ServiceHandler111(conf, wms, "localhost")
    wms130 = ServiceHandler130(conf, wms, "localhost")

    return (conf, {
        '1.1.1': wms111,
        '1.3.0': wms130
    })

def _check_style_lists(request, version, lyr_number, lyr_name, lyr_styles, exp_styles):
    n_lyr_styles = len(lyr_styles)
    n_exp_styles = len(exp_styles)
    n_min = min(n_lyr_styles, n_exp_styles)
    indent = ' ' * (len(request) + len(version) + 2)

    for lyr_style, exp_style, idx in zip(lyr_styles, exp_styles, range(n_min)):
        sys.stdout.write('%s style #%d \'%s\':' % (indent, idx+1, lyr_style))
        if lyr_style != exp_style:
            raise Exception('%s %s: Unexpected style #%d \'%s\' for layer #%d \'%s\': expected style: \'%s\'.' % (request, version, idx+1, lyr_style, lyr_number, lyr_name, exp_style))
        sys.stdout.write(' OK' + os.linesep)

    if n_lyr_styles < n_exp_styles:
        s = ''
        for style in exp_styles[n_lyr_styles:]:
            s += '\'%s\', ' % style
        s = s[:len(s)-2]
        raise Exception('%s %s: Missing %d style(s) for layer #%d \'%s\': missing style(s): %s.' % (request, version, n_exp_styles-n_lyr_styles, lyr_number, lyr_name, s))

    if n_lyr_styles > n_exp_styles:
        s = ''
        for style in lyr_styles[n_exp_styles:]:
            s += '\'%s\', ' % style
        s = s[:len(s)-2]
        raise Exception('%s %s: Found %d unexpected style(s) for layer #%d \'%s\': unexpected styles: %s.' % (request, version, n_lyr_styles-n_exp_styles, lyr_number, lyr_name, s))


def test_capabilities():
    from xml.etree import ElementTree

    def get_caps_styles(xml_string, ns=''):

        result = []
        caps_dom = ElementTree.XML(xml_string)

        for lyr_dom in caps_dom.findall('%sCapability/%sLayer/%sLayer' % (ns, ns, ns)):
            lyr_name = lyr_dom.findtext('%sName' % ns)
            if lyr_name:
                styles = []
                for style in lyr_dom.findall('%sStyle' % ns):
                    name = style.findtext('%sName' % ns)
                    title = style.findtext('%sTitle' % ns)
                    abstr = style.findtext('%sAbstract' % ns)
                    styles.append((name, title, abstr))

                result.append((lyr_name, styles))

        return result

    def check_caps_styles(store, version, no, layer, styles):

        print 'GetCapabilities %s: layer #%d \'%s\':' % (version, no, layer)

        lyr = store[no-1]
        if (lyr[0] != layer):
            raise Exception('GetCapabilities %s: Unexpected name \'%s\' for layer #%d: expected name: \'%s\'.' % (version, lyr[0], no, layer))

        lyr_styles = lyr[1]
        if len(lyr_styles) == 0:
            raise Exception('GetCapabilities %s: No styles found for layer \'%s\'.' % (version, lyr[0]))

        _check_style_lists('GetCapabilities', version, no, layer, [x[0] for x in lyr_styles], styles)

        if len(styles) > 1 and lyr_styles[0][2] == None:
            raise Exception('GetCapabilities %s: Missing Abstract text for default style #1 \'%s\' of layer #%d \'%s\'.' % (version, lyr_styles[0][0], no, lyr[0]))


    conf, services = _wms_services('mapfile_styles.xml')

    for version, ns in [('1.1.1', ''), ('1.3.0', '{http://www.opengis.net/wms}')]:

        caps = services[version].GetCapabilities({}).content
        styles = get_caps_styles(caps, ns)

        print
        print 'GetCapabilities %s: collected layers and styles:' % version
        print
        print styles
        print

        check_caps_styles(styles, version, 1, 'single-style-layer', ['simple-style'])
        check_caps_styles(styles, version, 2, 'multi-style-layer', ['default', 'simple-style', 'another-style'])
        check_caps_styles(styles, version, 3, 'awkward-layer', ['default', 'another-style'])
        check_caps_styles(styles, version, 4, 'single-default-layer', ['default'])

    return True

def test_map():
    from ogcserver.WMS import ServiceHandlerFactory

    reqparams = {
        'srs': 'EPSG:4326',
        'bbox': '-180.0000,-90.0000,180.0000,90.0000',
        'width': 800,
        'height': 600,
        'layers': '__all__',
        'styles': '',
        'format': 'image/png',
    }

    def check_map_styles(version, no, layer, style_param, styles=None):
        
        print 'GetMap %s: layer #%d \'%s\': STYLES=%s' % (version, no, layer, style_param)

        ogcparams['layers'] = layer.split(',')
        ogcparams['styles'] = style_param.split(',')

        # Parameter 'styles' contains the list of expected styles. If styles
        # evaluates to False (e.g. None, Null), an invalid STYLE was provided
        # and so, an OGCException 'StyleNotDefined' is expected.
        try:
            m = services[version]._buildMap(ogcparams)
        except OGCException:
            if not styles:
                print '              style #0 \'invalid style\': OK (caught OGCException)'
                print
                return
            raise Exception('GetMap %s: Expected OGCExecption for invalid style \'%s\' for layer #%d \'%s\' was not thrown.' % (version, style_param, no, layer))

        _check_style_lists('GetMap', version, no, layer, m.layers[0].styles, styles)
        print
                                             

    conf, services = _wms_services('mapfile_styles.xml')
    
    mapfactory = BaseWMSFactory() 
    servicehandler = ServiceHandlerFactory(conf, mapfactory, '', '1.1.1')
    ogcparams = servicehandler.processParameters('GetMap', reqparams)
    ogcparams['crs'] = ogcparams['srs']
    ogcparams['HTTP_USER_AGENT'] = 'unit_tests'

    for version in ['1.1.1', '1.3.0']:
        check_map_styles(version, 1, 'single-style-layer', '', ['simple-style'])
        check_map_styles(version, 1, 'single-style-layer', 'simple-style', ['simple-style'])
        check_map_styles(version, 1, 'single-style-layer', 'default')
        check_map_styles(version, 1, 'single-style-layer', 'invalid-style')
        
        check_map_styles(version, 2, 'multi-style-layer', '', ['simple-style', 'another-style'])
        check_map_styles(version, 2, 'multi-style-layer', 'default', ['simple-style', 'another-style'])
        check_map_styles(version, 2, 'multi-style-layer', 'simple-style', ['simple-style'])
        check_map_styles(version, 2, 'multi-style-layer', 'another-style', ['another-style'])
        check_map_styles(version, 2, 'multi-style-layer', 'invalid-style')

        check_map_styles(version, 3, 'awkward-layer', '', ['default', 'another-style'])
        check_map_styles(version, 3, 'awkward-layer', 'default', ['default', 'another-style'])
        check_map_styles(version, 3, 'awkward-layer', 'another-style', ['another-style'])
        check_map_styles(version, 3, 'awkward-layer', 'invalid-style')

        check_map_styles(version, 4, 'single-default-layer', '', ['default'])
        check_map_styles(version, 4, 'single-default-layer', 'default', ['default'])
        check_map_styles(version, 4, 'single-default-layer', 'invalid-style')

        # Some 'manually' created error cases for testing error reporting
        #check_map_styles(version, 2, 'multi-style-layer', 'default', ['simple-style', 'another-style', 'foo', 'bar'])
        #check_map_styles(version, 2, 'multi-style-layer', 'default', ['simple-style'])
        
    return True


# Running the tests without nose
#test_capabilities()
#test_map()      
