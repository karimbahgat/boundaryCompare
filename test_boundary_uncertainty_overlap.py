
import boundarytools
import numpy as np

import json
from urllib.request import urlopen

# params
SIGNED = False

# setup data
country = 'CIV'

topoj = json.loads(urlopen('https://media.githubusercontent.com/media/wmgeolab/geoContrast/main/releaseData/naturalEarth/{country}/ADM1/naturalEarth-{country}-ADM1.topojson'.format(country=country)).read())
coll1 = boundarytools.utils.topo2geoj(topoj)
for f in coll1['features']:
    if f['properties']['name'] == 'Denguélé':
    #if f['properties']['name'] == 'Savanes':
    #if f['properties']['name'] == 'Zanzan':
        feat1 = f
        break

topoj = json.loads(urlopen('https://media.githubusercontent.com/media/wmgeolab/geoContrast/main/releaseData/gadm/{country}/ADM1/gadm-{country}-ADM1.topojson'.format(country=country)).read())
coll2 = boundarytools.utils.topo2geoj(topoj)
for f in coll2['features']:
    if f['properties']['NAME_1'] == 'Denguélé':
    #if f['properties']['NAME_1'] == 'Savanes':
    #if f['properties']['NAME_1'] == 'Zanzan':
        feat2 = f
        break

topoj = json.loads(urlopen('https://media.githubusercontent.com/media/wmgeolab/geoContrast/main/releaseData/CIV_CNTIG/{country}/ADM1/CIV_CNTIG-{country}-ADM1.topojson'.format(country=country)).read())
coll3 = boundarytools.utils.topo2geoj(topoj)
for f in coll3['features']:
    if f['properties']['ADM1_FR'] == 'Kabadougou': # ca 60% of Denguele
    #if f['properties']['ADM1_FR'] == 'Savanes':
    #if f['properties']['ADM1_FR'] == 'Zanzan':
        feat3 = f
        break

#feat1,feat2 = feat2,feat1 # see if switching has an effect

assert feat1 and feat2

def compare(geom1, geom2):
    # params
    # ... 
    
    # data 1
    bnd1 = boundarytools.uncertainty.NormalBoundary(geom1)
    res = bnd1.precision_range_max / 5.0
    print(bnd1.precision, bnd1.precision_range_max, res)
    #bnd1.show(bnd1.uncertainty_surface(res))

    # data 2
    bnd2 = boundarytools.uncertainty.NormalBoundary(geom2)
    res = bnd2.precision_range_max / 5.0
    print(bnd2.precision, bnd2.precision_range_max, res)
    #bnd2.show(bnd2.uncertainty_surface(res))

    # both
    res = min(bnd1.precision_range_max, bnd2.precision_range_max) / 5.0

    # probability

    # show joint probability surface (all occur simultaneously)
    joint = boundarytools.compare.joint_probability_surface(bnd1, bnd2, resolution=res)
    bnd1.show(surf=joint)

    # show disjoint probability surface (all do not occur simultaneously)
    disjoint = boundarytools.compare.disjoint_probability_surface(bnd1, bnd2, resolution=res)
    bnd1.show(surf=disjoint)

    # certain one way or the other
    certain = np.maximum(joint, disjoint)
    boundarytools.utils.show_boundaries([bnd1,bnd2], surf=certain)

    # uncertain of either
    # either joint or disjoint (ie not joint and not disjoint)
    # ie the places we are uncertain of, cannot tell one way or another
    uncertain = 1 - certain # not certain
    boundarytools.utils.show_boundaries([bnd1,bnd2], surf=uncertain)

    # fuzzyness

    # show overlap
    surf1,surf2,overlap = bnd1.overlap_surface(bnd2, resolution=res)
    bnd1.show(surf=overlap)

    # show difference
    surf1,surf2,diff = bnd1.difference_surface(bnd2, resolution=res)
    bnd1.show(surf=diff)

    # stats test
    stats = bnd1.similarity(bnd2, resolution=res)
    print(stats)

def compare_multi(*feats, thresh):
    boundaries = [boundarytools.uncertainty.NormalBoundary(feat['geometry']) for feat in feats]

    # resolution
    res = min(bnd.precision_range_max for bnd in boundaries) / 2.0
    print('resolution', res)

    # show joint probability surface (all occur simultaneously)
    joint = boundarytools.compare.joint_probability_surface(*boundaries, resolution=res)
    boundarytools.utils.show_boundaries(boundaries, surf=joint)

    # print share of boundary1 area above 95% probability
    b1 = boundaries[0]
    b1surf = b1.uncertainty_surface(resolution=res)
    b1area = (b1surf>=0.5).sum() # 0.5 is the dividing line between the inside and outside of the original boundary
    jointarea = (joint>=thresh).sum()
    share = jointarea / b1area * 100
    print('area above {}% probability (from the perspective of boundary1)'.format(round(thresh*100)), round(share,1), '%')

    # show disjoint probability surface (all do not occur simultaneously)
    disjoint = boundarytools.compare.disjoint_probability_surface(*boundaries, resolution=res)
    boundarytools.utils.show_boundaries(boundaries, surf=disjoint)

    # certain one way or the other
    certain = np.maximum(joint, disjoint)
    boundarytools.utils.show_boundaries(boundaries, surf=certain)

    # uncertain of either
    # either joint or disjoint (ie not joint and not disjoint)
    # ie the places we are uncertain of, cannot tell one way or another
    uncertain = 1 - certain # not certain
    boundarytools.utils.show_boundaries(boundaries, surf=uncertain)

def uncertain_territory(feat, thresh):
    bnd = boundarytools.uncertainty.NormalBoundary(feat['geometry'])
    res = bnd.precision_range_max / 2.0
    surf = bnd.uncertainty_surface(resolution=res)
    bnd.show(surf)

    barea = (surf>=0.5).sum() # 0.5 is the dividing line between the inside and outside of the original boundary
    certarea = (surf>=thresh).sum()
    certshare = certarea / barea * 100
    uncertshare = 100 - certshare
    print('area below {}% probability ie uncertain'.format(round(thresh*100)), round(uncertshare,1), '%')


### individual source uncertainty

##print('b1')
##uncertain_territory(feat1, 0.99)
##print('b2')
##uncertain_territory(feat2, 0.99)
##print('b3')
##uncertain_territory(feat3, 0.99)


### compare

# old
compare(feat1['geometry'], feat2['geometry'])

# new
compare_multi(feat1, feat2, thresh=0.99) #, feat3)




    
