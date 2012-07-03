#!/usr/bin/env python

try:
    from setuptools import setup
    HAS_SETUPTOOLS = True
except ImportError:
    from distutils.core import setup
    HAS_SETUPTOOLS = False

options = dict(name='ogcserver',
    version='0.1.0',
    description="A OGC WMS for Mapnik",
    #long_description="TODO",
    author='Jean-Francois Doyon',
    maintainer='Dane Springmeyer',
    maintainer_email='dane@dbsgeo.com',
    requires=['mapnik (>=0.7.0)'],
    provides=['ogcserver'],
    keywords='mapnik,wms,gis,geospatial',
    url='https://github.com/mapnik/OGCServer',
    packages=['ogcserver'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'License :: OSI Approved :: BSD License',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering :: GIS',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Utilities'],
)

if HAS_SETUPTOOLS:
    options.update(dict(entry_points={
        'paste.app_factory': ['mapfile=ogcserver.wsgi:ogcserver_map_factory',
                              'wms_factory=ogcserver.wsgi:ogcserver_wms_factory',
                             ],
    },
    install_requires = ['setuptools', 'PasteScript', 'WebOb', 'lxml', 'PIL']
    ))

setup(**options)

if not HAS_SETUPTOOLS:
    warning = '\n***Warning*** ogcserver also requires'
    missing = False
    try:
        import PIL
        # todo import Image ?
    except:
        try:
            import Image
        except:
            missing = True
            warning +=' PIL (easy_install PIL)'
    try:
        import lxml
    except:
        missing = True
        warning +' lxml (easy_install lxml)'
    if missing:
        import sys
        sys.stderr.write('%s\n' % warning)

