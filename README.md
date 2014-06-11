
# Ogcserver

Python WMS implementation using Mapnik.

## Depends

    Mapnik >= 0.7.0 (and python bindings)
    Pillow
    PasteScript
    WebOb

You will need to install Mapnik separately.

All the remaining dependencies should be installed cleanly with the command below.


## Install
    
Run the following command inside this directory (the directory that also contains the 'setup.py' file):

    sudo python setup.py install


## Testing

Run the local http server with the sample data:

    ogcserver demo/map.xml

Viewing http://localhost:8000/ in a local browser should show a welcome message like 'Welcome to the OGCServer'

Now you should be able to access a map tile with a basic WMS request like:

    http://localhost:8000/?LAYERS=__all__&STYLES=&FORMAT=image%2Fpng&SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&SRS=EPSG%3A3857&BBOX=-20037508.34,-20037508.34,20037508.3384,20037508.3384&WIDTH=256&HEIGHT=256
    

