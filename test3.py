
import boundarytools

import topojson
import json

from urllib.request import urlopen

import warnings
warnings.filterwarnings("ignore")

def compare(geom1, geom2, resolution=None):
    # data 1
    bnd1 = boundarytools.uncertainty.NormalBoundary(geom1, mean=0, stdev=0)
    #bnd1.show(bnd1.uncertainty_surface(res))

    # data 2
    bnd2 = boundarytools.uncertainty.NormalBoundary(geom2, mean=0, stdev=0)
    #bnd2.show(bnd2.uncertainty_surface(res))

    # show overlap
    #surf1,surf2,overlap = bnd1.overlap_surface(bnd2)
    #bnd1.show(surf=overlap)

    # show difference
    #surf1,surf2,diff = bnd1.difference_surface(bnd2)
    #bnd1.show(surf=diff)

    # stats test
    stats = bnd1.similarity(bnd2, resolution=resolution)
    return stats

def show_datasets(data1, data2):
    import matplotlib.pyplot as plt
    from shapely.geometry import asShape
    # setup plot
    plt.clf()
    ax = plt.gca()
    ax.set_aspect('equal', 'datalim')
    # data1
    for feat in data1['features']:
        for ring in boundarytools.utils.iter_rings(feat['geometry']):
            ring = list(ring)
            if ring[0]!=ring[-1]: ring.append(ring[-1])
            x,y = zip(*ring)
            plt.plot(x, y, color='tab:blue', marker='')
    # data2
    for feat in data2['features']:
        for ring in boundarytools.utils.iter_rings(feat['geometry']):
            ring = list(ring)
            if ring[0]!=ring[-1]: ring.append(ring[-1])
            x,y = zip(*ring)
            plt.plot(x, y, color='tab:red', marker='')
    plt.show()

def calc_stats(feat, comparisons, resolution=None):
    # calc stats for all pairs
    all_stats = []
    for comp in comparisons:
        st = compare(feat['geometry'], comp['geometry'], resolution=resolution)
        all_stats.append((comp,st))

    return all_stats

def sort_stats(stats, key, thresh=0.9):
    # sort by most equal
    stats = sorted(stats, key=lambda x: -x[1][key])

    # filter only those above thresh
    stats = [(comp,st) for comp,st in stats
                 if st[key] >= thresh]

    return stats

def equals(stats, thresh=0.95):
    return sort_stats(stats, 'equality', thresh)

def contains(stats, thresh=0.95):
    return sort_stats(stats, 'contains', thresh)

def belongs(stats, thresh=0.95):
    return sort_stats(stats, 'within', thresh)

#########################

from topojson.utils import geometry
import numpy as np
def topo2geoj(data):
    lyr = list(data['objects'].keys())[0]
    tfeatures = data['objects'][lyr]['geometries']
    data['arcs'] = [np.array(arc) for arc in data['arcs']] # topojson.utils.geometry() assumes np arrays
    geoj = {'type': "FeatureCollection", 'features': []}
    for tfeat in tfeatures:
        #print(tfeat['type'], tfeat['properties']) #, tfeat['arcs']) 
        feat = {'type': "Feature"}
        feat['properties'] = tfeat['properties'].copy()
        feat['geometry'] = geometry(tfeat, data['arcs'], data.get('transform'))
        geoj['features'].append(feat)
    return geoj

# setup data
country = 'CIV'

topoj = json.loads(urlopen('https://media.githubusercontent.com/media/wmgeolab/geoContrast/main/releaseData/naturalEarth/{country}/ADM1/naturalEarth-{country}-ADM1.topojson'.format(country=country)).read())
coll1 = topo2geoj(topoj)
for f in coll1['features']:
    f['properties']['_name'] = f['properties']['name']

topoj = json.loads(urlopen('https://media.githubusercontent.com/media/wmgeolab/geoContrast/main/releaseData/gadm/{country}/ADM1/gadm-{country}-ADM1.topojson'.format(country=country)).read())
coll2 = topo2geoj(topoj)
for f in coll2['features']:
    f['properties']['_name'] = f['properties']['NAME_1']

##topoj = json.loads(urlopen('https://media.githubusercontent.com/media/wmgeolab/geoContrast/main/releaseData/CIV_CNTIG/{country}/ADM1/CIV_CNTIG-{country}-ADM1.topojson'.format(country=country)).read())
##coll2 = topo2geoj(topoj)
##for f in coll2['features']:
##    f['properties']['_name'] = f['properties']['ADM1_FR']

print(len(coll1['features']), 'vs', len(coll1['features']))

show_datasets(coll1, coll2)

# find closest matches for each unit (old classification version...)
for feat in coll1['features']:
    print(feat['properties']['name'])
    allstats = calc_stats(feat, coll2['features'], resolution=0.05)
    # find equals
    matches = equals(allstats)
    for match,stats in matches:
        print('--> EQUALS:', match['properties']['NAME_1'], stats['equality'])
    if matches:
        continue
    # find children (ie covers multiple units in comparison dataset)
    matches = contains(allstats)
    for match,stats in matches:
        print('--> CONTAINS:', match['properties']['NAME_1'], stats['contains'], '({} of total area)'.format(stats['within']))
    if matches:
        continue
    # find parent (ie is contained by another unit in comparison dataset)
    matches = belongs(allstats)
    for match,stats in matches:
        print('--> BELONGS TO:', match['properties']['NAME_1'], stats['within'], '({} of total area)'.format(stats['contains']))
    if matches:
        continue
    # other
    matches = contains(allstats, 0.05)
    for match,stats in matches:
        print('--> PARTIALLY CONTAINS:', match['properties']['NAME_1'], stats['contains'], '({} of total area)'.format(stats['within']))
    matches = belongs(allstats, 0.05)
    for match,stats in matches:
        print('--> PARTIALLY BELONGS TO:', match['properties']['NAME_1'], stats['within'], '({} of total area)'.format(stats['contains']))


fdfdasfa












    
# find closest equals
##print('### A EQUALS B')
##for feat in coll1['features']:
##    allstats = calc_stats(feat, coll2['features'])
##    # find matches
##    matches = equals(allstats)
##    for match,stats in matches:
##        print('-->', feat['properties']['_name'], 'EQUALS', match['properties']['_name'], stats['equality'])

# find closest contains
print('\n### A CONTAINS B')
for feat in sorted(coll1['features'], key=lambda f: f['properties']['_name']):
    allstats = calc_stats(feat, coll2['features'])
    # find matches
    matches = belongs(allstats, 0) # get all sorted by within
    matches = [(comp,st) for comp,st in matches if (st['contains']>=0.1 or st['within']>=0.1)]
    if len(matches) > 0:
        if len(matches) == 1:
            relation = 'IS'
        else:
            relation = 'CONTAINS'
        print('-->', feat['properties']['_name'], relation)
        for match,stats in matches:
            if len(matches) == 1:
                if stats['equality'] >= 0.95:
                    relation = 'EQUAL TO'
                    stat = stats['equality']
                else:
                    relation = 'A SUBSET OF'
                    stat = stats['contains']
            elif stats['contains'] >= 0.95:
                relation = 'ALL OF'
                stat = stats['within']
            else:
                relation = 'PARTS OF'
                stat = stats['within']
            print('\t'*1, relation, match['properties']['_name'], stat)

# find closest contains (reversed)
print('\n### B CONTAINS A')
for feat in sorted(coll2['features'], key=lambda f: f['properties']['_name']):
    allstats = calc_stats(feat, coll1['features'])
    # find matches
    matches = belongs(allstats, 0) # get all sorted by within
    matches = [(comp,st) for comp,st in matches if (st['contains']>=0.1 or st['within']>=0.1)]
    if len(matches) > 0:
        if len(matches) == 1:
            relation = 'IS'
        else:
            relation = 'CONTAINS'
        print('-->', feat['properties']['_name'], relation)
        for match,stats in matches:
            if len(matches) == 1:
                if stats['equality'] >= 0.95:
                    relation = 'EQUAL TO'
                    stat = stats['equality']
                else:
                    relation = 'A SUBSET OF'
                    stat = stats['contains']
            elif stats['contains'] >= 0.95:
                relation = 'ALL OF'
                stat = stats['within']
            else:
                relation = 'PARTS OF'
                stat = stats['within']
            print('\t'*1, relation, match['properties']['_name'], stat)
