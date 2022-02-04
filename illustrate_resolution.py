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
    m.add_layer(d, fillcolor=(170,170,170), outlinecolor='blue', outlinewidth='3px')
    m.add_layer(d.convert.to_points('vertex'), fillcolor='blue', fillsize='5px', outlinecolor=None)

    # source2
    d = pg.VectorData()
    d.fields = list(geoj2['features'][0]['properties'].keys())
    for f in geoj2['features']:
        d.add_feature(f['properties'], f['geometry'])
    d = d.select(zoomfunc2)
    m.add_layer(d, fillcolor=None, outlinecolor='red', outlinewidth='3px')
    m.add_layer(d.convert.to_points('vertex'), fillcolor='red', fillsize='5px', outlinecolor=None)

    bbox = m.layers[0].data.bbox
    print(bbox)
    w,h = bbox[2]-bbox[0], bbox[3]-bbox[1]
    bbox = [bbox[0], bbox[1], bbox[0]+w/4.0, bbox[1]+h/4.0]
    print(bbox)

    for r in get_landsat_raster(bbox):
        print(r)
        m.add_layer(r)
    
    m.zoom_bbox(*bbox, geographic=True)
    m.zoom_out(1.1)
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





    
