# imports
import boundarytools
import os
import json
import numpy as np
import math
import csv
from urllib.request import urlopen
import pythongis as pg

# params
BRANCH = 'gadm4'
SOURCES = ['geoBoundaries (Open)', 'GADM', 'OpenStreetMap', 'SALB', 'OCHA', 'Natural_Earth']

# load country boundaries
#url = 'https://www.geoboundaries.org/data/geoBoundariesCGAZ-3_0_0/ADM0/simplifyRatio_10/geoBoundariesCGAZ_ADM0.geojson'
#geoj = boundarytools.utils.load_geojson_url(url)
with open('data/gb-countries-simple.json') as r:
    geoj = json.loads(r.read())
    
# collect stats
def load_meta():
    url = f'https://raw.githubusercontent.com/wmgeolab/geoContrast/{BRANCH}/releaseData/geoContrast-meta.csv'
    raw = urlopen(url).read().decode('utf8')
    print(len(raw), raw[:100])
    reader = csv.DictReader(raw.split('\n'))
    return list(reader)
      
META = load_meta()
    
def get_country_level_stats(iso, level):
    # open source pair stats
    countrylevelrows = [r
                        for r in META
                        if r['boundaryISO']==iso
                        and r['boundaryType']=='ADM{}'.format(level)
                       ]
    if SOURCES:
        countrylevelrows = [r for r in countrylevelrows
                            if r['boundaryCollection'] in SOURCES]
    yrs = [r['boundaryYearRepresented'] for r in countrylevelrows]
    yrs = [int(yr) for yr in yrs if yr != 'Unknown']
    stats = {}
    stats['yr_max'] = np.max(yrs) if yrs else None
    stats['yr_mean'] = np.mean(yrs) if yrs else None
    stats['yr_std'] = np.std(yrs) if yrs else None
    return stats
      
# collect for each level
for f in geoj['features']:
    props = f['properties']
    iso = props['shapeISO']
    #print(iso)
    for level in range(0, 4+1):
        #print('ADM',level)
        stats = get_country_level_stats(iso, level)
        if stats:
            #print(stats)
            for k,v in stats.items():
                k = k + str(level)
                props[k] = v
            
# some figure configs
import matplotlib.pyplot as plt
plt.rcParams['axes.grid'] = False
plt.rcParams['lines.linewidth'] = 0.5

breaks = 'equal'
classes = 5
colors = [(146,3,85), (230,230,230), (45,107,26)] # ['red','white','green']

def save_map(geoj, color_by, title, output, reverse_colors=False):
    d = pg.VectorData()
    d.fields = list(geoj['features'][0]['properties'].keys())
    for f in geoj['features']:
        if f['properties']['shapeName'] == 'Antarctica':
            continue
        d.add_feature(f['properties'], f['geometry'])
    print(d)
    m = pg.renderer.Map(4000,2000,background='lightblue')
    m.zoom_bbox(-180,-70,180,90)
    if reverse_colors:
        _colors = list(reversed(colors))
    else:
        _colors = colors
    m.add_layer(d, fillcolor='gray', outlinewidth='0.3px',
                transparency=0.3, legend=False)
    m.add_layer(d.select(lambda f: f[color_by] != None),
                fillcolor={'key':color_by,
                              'breaks':breaks,
                              'classes':classes,
                              'colors':_colors},
                outlinewidth='2.5px',
                legendoptions={'title':title, 'valueformat':lambda v: format(v,'.0f')}) #, 'direction':'e'})
    m.add_legend({'fillcolor':None,'outlinecolor':None})#, xy=('50%w','99%h'), anchor='s')
    m.save(output)
            
# visualize country year stdev
for level in range(0, 4+1):
    print(level)
    #fig = boundarytools.utils.show_dataset(geoj, color_by='yr_std{}'.format(level))
    #fig.savefig('figures/yr_std{}.png'.format(level))
    save_map(geoj, 'yr_std{}'.format(level),
             'ADM{} Boundary\nYear Variation'.format(level),
             'figures/yr_std{}.png'.format(level),
             reverse_colors=True)
    
    #fig = boundarytools.utils.show_dataset(geoj, color_by='yr_mean{}'.format(level))
    #fig.savefig('figures/yr_mean{}.png'.format(level))
    save_map(geoj, 'yr_mean{}'.format(level),
             'ADM{} Average\nBoundary Year'.format(level),
             'figures/yr_mean{}.png'.format(level))
    
    #fig = boundarytools.utils.show_dataset(geoj, color_by='yr_mean{}'.format(level))
    #fig.savefig('figures/yr_max{}.png'.format(level))
    save_map(geoj, 'yr_max{}'.format(level),
             'ADM{} Latest\nBoundary Year'.format(level),
             'figures/yr_max{}.png'.format(level))

    
