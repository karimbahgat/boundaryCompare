# imports
import boundarytools as bt
import os
import json
import numpy as np
import math
import csv
from urllib.request import urlopen
import pythongis as pg

# load country boundaries
#url = 'https://www.geoboundaries.org/data/geoBoundariesCGAZ-3_0_0/ADM0/simplifyRatio_10/geoBoundariesCGAZ_ADM0.geojson'
#geoj = boundarytools.utils.load_geojson_url(url)
with open('data/gb-countries-simple.json') as r:
    geoj = json.loads(r.read())
countries = pg.VectorData()
countries.fields = list(geoj['features'][0]['properties'].keys())
print(countries.fields)
for f in geoj['features']:
    countries.add_feature(f['properties'], f['geometry'])

'''
def get_landsat_raster(bbox):
    from landsatxplore.api import API
    user = 'kbahgat'
    pw = input('Please input Earth Explorer password:\n>>> ')
    landsat_api = API(user, pw)

    print(bbox)
    dataset = 'landsat_8_c1'
    scenes = landsat_api.search(
        dataset=dataset,
        bbox=bbox,
        max_cloud_cover=10,
    )
    scenes = list(scenes)

    from landsatxplore.earthexplorer import EarthExplorer, EE_DOWNLOAD_URL, DATA_PRODUCTS
    ee = EarthExplorer(user, pw)
    for scene in scenes[:1]:
        print(scene)
        #path = ee.download(scene['entity_id'], 'temp')
        url = EE_DOWNLOAD_URL.format(
            data_product_id=DATA_PRODUCTS[dataset], entity_id=scene['entity_id']
        )
        path = ee._download(url, 'temp', timeout=300, chunk_size=1024*10)
        r = pg.RasterData(path)
        yield r
'''

# preload global satims
if 0:
    import urllib
    print('dl west')
    urllib.request.urlretrieve('https://eoimages.gsfc.nasa.gov/images/imagerecords/57000/57752/land_shallow_topo_west.tif',
                       'temp/land_shallow_topo_west.tif'
                      )
    print('dl east')
    urllib.request.urlretrieve('https://eoimages.gsfc.nasa.gov/images/imagerecords/57000/57752/land_shallow_topo_east.tif',
                       'temp/land_shallow_topo_east.tif'
                      )
    
# load global sat ims
print('open global sats')
import PIL.Image
PIL.Image.MAX_IMAGE_PIXELS = 466560000*2

scale = 180.0/21600
#affine = [scale,0,-180,
#         0,-scale,90]
#sat_west = pg.RasterData('temp/land_shallow_topo_west.tif', affine=affine)
#sat_west.set_geotransform(affine=affine)
affine = [scale,0,0,
         0,-scale,90]
sat_east = pg.RasterData('temp/land_shallow_topo_east.tif', affine=affine)
sat_east.set_geotransform(affine=affine)

def get_sat(bbox, padding=0):
    if padding:
        xmin,ymax,xmax,ymin = bbox
        w,h = abs(xmax-xmin),abs(ymax-ymin)
        xpad,ypad = w*padding, h*padding
        bbox = [xmin-xpad,ymax+ypad,xmax+xpad,ymin-ypad]
    if bbox[0] < 0:
        _bbox = list(bbox)
        _bbox[2] = min(0, _bbox[2])
        print(_bbox)
        yield sat_west.manage.crop(_bbox)
    if bbox[2] >= 0:
        _bbox = list(bbox)
        _bbox[0] = max(0, _bbox[0])
        print(_bbox)
        yield sat_east.manage.crop(_bbox)

# define map
def makemap(geoj, geoj2, zoomfunc, zoomfunc2, name):
    print(name)

    #crs = '+proj=aea +lat_1=27 +lat_2=45 +lat_0=35 +lon_0=105 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +no_defs'
    
    m = pg.renderer.Map(1200,1000,background='lightgray') #,crs=crs)

    # countries? 
    #m.add_layer(countries, fillcolor='lightgray', outlinewidth='0.5px')

    # source 1
    d = pg.VectorData()
    d.fields = list(geoj['features'][0]['properties'].keys())
    for f in geoj['features']:
        d.add_feature(f['properties'], f['geometry'])
    d = d.select(zoomfunc)
    m.add_layer(d, fillcolor=(222,222,255,55), outlinecolor='blue', outlinewidth='3px', legend=False)
    m.add_layer(d.convert.to_points('vertex'), fillcolor='blue', fillsize='5px', outlinecolor=None, legendoptions={'title':'geoBoundaries'})

    # source2
    d = pg.VectorData()
    d.fields = list(geoj2['features'][0]['properties'].keys())
    for f in geoj2['features']:
        d.add_feature(f['properties'], f['geometry'])
    d = d.select(zoomfunc2)
    m.add_layer(d, fillcolor=None, outlinecolor='red', outlinewidth='3px', legend=False)
    m.add_layer(d.convert.to_points('vertex'), fillcolor='red', fillsize='5px', outlinecolor=None, legendoptions={'title':'Natural Earth'})
    
    # zoom
    m.zoom_auto()
    #m.zoom_out(1.1)
    #m.zoom_in(3)
    m.offset('-35%w', '30%h')
    m.zoom_in(3)
    m.offset('-33%w', 0)
    m.zoom_in(3.5)

    # add satellite base layer
    bbox = m.bbox
    print(bbox)
    for sat in get_sat(bbox, padding=0.1):
    #for sat in [pg.RasterData('temp/localsat.tif')]: 
        for b in sat.bands:
            b.compute('min(val+10, 255)')
        m.add_layer(sat)
        m.move_layer(-1, 0)

    # save zoomed in map
    m.add_legend({'direction':'s', 'outlinecolor':None}) #, xy=('2%w','93%h'), anchor='sw')
    opts = dict(length=0.09,
                labeloptions={'textcolor':(255,255,255)},
                symboloptions={'fillcolor':(255,255,255)})
    m.add_scalebar(opts) #, xy=('4%w','98%h'), anchor='sw') 
    m.save('figures/resolution-{}-zoomed.png'.format(name))

    # create rectangle layer for current map view
    x1,y1,x2,y2 = bbox
    ring = [(x1,y1),(x2,y1),(x2,y2),(x1,y2),(x1,y1)]
    poly = {'type':'Polygon', 'coordinates':[ring]}
    d = pg.VectorData()
    d.add_feature([], poly)
    m.add_layer(d, fillcolor=None, outlinecolor="black", outlinewidth='5px', legend=False)

    # zoom out
    m.zoom_auto()
    m.zoom_out(1.1)

    # add satellite base layer for new zoom
    bbox = m.bbox
    print(bbox)
    for sat in get_sat(bbox, padding=0.1):
    #for sat in [pg.RasterData('temp/localsat.tif')]: 
        for b in sat.bands:
            b.compute('min(val+10, 255)')
        m.add_layer(sat)
        m.move_layer(-1, 0)

    # save zoomed out map with zoom rectangle
    m.render()
    m.save('figures/resolution-{}.png'.format(name))

# load data sources
iso,lvl = 'ETH', 1
sources = bt.utils.find_geocontrast_sources(iso, lvl)
geoj = bt.utils.load_topojson_url(sources['geoBoundaries (Open)'])
geoj2 = bt.utils.load_topojson_url(sources['Natural Earth v4.1'])
zoomfunc = lambda f: f['shapeName']=='Tigray'
zoomfunc2 = lambda f: f['name']=='Tigray'
name = '{}-{}-Tigray-gB vs NE'.format(iso, lvl)
makemap(geoj, geoj2, zoomfunc, zoomfunc2, name)





    
