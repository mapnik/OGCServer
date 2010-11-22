#!/usr/bin/env python

try:
    from setuptools import setup
except:
    from distutils.core import setup

setup(name='ogcserver',
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
