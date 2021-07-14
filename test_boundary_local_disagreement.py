# TODO:
# comparing two units might be possible after all, eg by creating a boundary ID raster showing the most likely unit in each source
# then can compare each unique pair of boundary IDs from each source and calc the disjoint prob surface
# and for each pair burn the disagreement prob surface onto a final output for those pixels

import boundarytools
import numpy as np

import json
from urllib.request import urlopen

# params
SIGNED = False

# setup data
country = 'CIV' #'TUN' #'BDI' #'BLR' #'LUX' #'CHE'

topoj = json.loads(urlopen('https://media.githubusercontent.com/media/wmgeolab/geoContrast/main/releaseData/naturalEarth/{country}/ADM1/naturalEarth-{country}-ADM1.topojson'.format(country=country)).read())
coll1 = boundarytools.utils.topo2geoj(topoj)

topoj = json.loads(urlopen('https://media.githubusercontent.com/media/wmgeolab/geoContrast/main/releaseData/gadm/{country}/ADM1/gadm-{country}-ADM1.topojson'.format(country=country)).read())
coll2 = boundarytools.utils.topo2geoj(topoj)

##topoj = json.loads(urlopen('https://media.githubusercontent.com/media/wmgeolab/geoContrast/main/releaseData/CIV_CNTIG/{country}/ADM1/CIV_CNTIG-{country}-ADM1.topojson'.format(country=country)).read())
##coll3 = boundarytools.utils.topo2geoj(topoj)

#################

def probability_local_disagreement(feats1, feats2, resolution=None, bbox=None):
    boundaries1 = [boundarytools.uncertainty.NormalBoundary(feat['geometry']) for feat in feats1]
    print('boundaries1', len(boundaries1))
    boundaries2 = [boundarytools.uncertainty.NormalBoundary(feat['geometry']) for feat in feats2]
    print('boundaries2', len(boundaries2))

    # resolution
    if not resolution:
        ranges = [bnd.precision_range_max for bnd in boundaries1] + [bnd.precision_range_max for bnd in boundaries2]
        resolution = min(ranges) / 2.0
        print('resolution', resolution)

    # get bboxes
    if not bbox:
        bboxes = [b.uncertainty_bbox() for b in boundaries1] + [b.uncertainty_bbox() for b in boundaries2]
        bbox = boundarytools.utils.bbox_union(*bboxes)

    # precalc
##    print('precalc1')
##    for bnd in boundaries1:
##        print(bnd)
##        bnd._inside = bnd.uncertainty_surface(resolution, bbox=bbox)
##    print('precalc2')
##    for bnd in boundaries2:
##        print(bnd)
##        bnd._inside = bnd.uncertainty_surface(resolution, bbox=bbox)

    # probability of being inside any of the boundaries
    cumul = None
    for i,bnd1 in enumerate(boundaries1):
        print('bnd1',i+1,bnd1)
        for i2,bnd2 in enumerate(boundaries2):
            print('--> bnd2',i2+1,bnd2)
            isec = bnd1.bbox_intersection(bnd2)
            if isec:
                if not hasattr(bnd1, '_inside'):
                    bnd1._inside = bnd1.uncertainty_surface(resolution=resolution, bbox=bbox)
                if not hasattr(bnd2, '_inside'):
                    bnd2._inside = bnd2.uncertainty_surface(resolution=resolution, bbox=bbox)
                inside1 = bnd1._inside
                inside2 = bnd2._inside
                joint = inside1 * inside2
                #boundarytools.utils.show_boundaries([bnd1], inside1, bbox=bbox)
                #boundarytools.utils.show_boundaries([bnd2], inside2, bbox=bbox)
                
                # only compare those that make up more than half of area in the other boundary
                # NOT SURE IF THAT IS THE RIGHT APPROACH... 
                if (joint.sum() / inside2.sum()) >= 0.5: 
                    notjoint = 1 - joint
                    uniq = inside1*notjoint + inside2*notjoint # (b1 AND NOT intersection) OR (b2 AND NOT INTERSECTION)
                    #boundarytools.utils.show_boundaries([bnd1,bnd2], uniq, bbox=bbox)
                    if cumul is None:
                        cumul = uniq
                    else:
                        cumul = np.maximum(cumul, uniq)
                        
                    #boundarytools.utils.show_boundaries([bnd1,bnd2], cumul, bbox=bbox)
        
##        inside = bnd._inside #bnd.uncertainty_surface(resolution, bbox=bbox)
##        #bnd.show(inside, bbox=bbox)
##        # get the probability inside our boundary AND not inside any other boundary
##        certinside = inside
##        for bnd2 in boundaries:
##            if bnd2 is bnd:
##                continue
##            notinsideother = 1 - bnd2._inside
##            certinside *= notinsideother
##        #bnd.show(certinside, bbox=bbox)
##        # add to cumul
##        if cumul is None:
##            cumul = certinside
##        else:
##            cumul += certinside
##        #bnd.show(cumul, bbox=bbox)

    return cumul

def probability_inside(feats, resolution=None, bbox=None):
    boundaries = [boundarytools.uncertainty.NormalBoundary(feat['geometry']) for feat in feats]
    print('boundaries', len(boundaries))

    # resolution
    if not resolution:
        resolution = min(bnd.precision_range_max for bnd in boundaries) / 4.0
        print('resolution', resolution)

    # get bboxes
    if not bbox:
        bboxes = [b.uncertainty_bbox() for b in boundaries]
        bbox = boundarytools.utils.bbox_union(*bboxes)

    # precalc
    print('precalc')
    for bnd in boundaries:
        print(bnd)
        bnd._inside = bnd.uncertainty_surface(resolution, bbox=bbox)

    # probability of being inside any of the boundaries
    cumul = None
    for bnd in boundaries:
        inside = bnd._inside #bnd.uncertainty_surface(resolution, bbox=bbox)
        #bnd.show(inside, bbox=bbox)
        # get the probability inside our boundary AND not inside any other boundary
        certinside = inside
        for bnd2 in boundaries:
            if bnd2 is bnd:
                continue
            notinsideother = 1 - bnd2._inside
            certinside *= notinsideother
        #bnd.show(certinside, bbox=bbox)
        # add to cumul
        if cumul is None:
            cumul = certinside
        else:
            cumul += certinside
        #bnd.show(cumul, bbox=bbox)

    #boundarytools.utils.show_boundaries(boundaries, cumul, bbox=bbox)
    return cumul



### boundaries
##boundaries1 = [boundarytools.uncertainty.NormalBoundary(feat['geometry']) for feat in coll1['features']]
##boundaries2 = [boundarytools.uncertainty.NormalBoundary(feat['geometry']) for feat in coll2['features']]
##
### resolution
##res1 = min(bnd.precision_range_max for bnd in boundaries1) / 2.0
##res2 = min(bnd.precision_range_max for bnd in boundaries2) / 2.0
##print(res1,res2)
##res = min(res1,res2)
##print('resolution', res)
##
### get bboxes
##bboxes = [b.uncertainty_bbox() for b in boundaries1] + [b.uncertainty_bbox() for b in boundaries2]
##bbox = boundarytools.utils.bbox_union(*bboxes)

# params
res = 0.01




# get diff
diff = probability_local_disagreement(coll1['features'], coll2['features'], resolution=res) #, bbox=bbox)

# show
boundarytools.utils.show_surface(diff)

# calc diff stats
allinside1 = probability_inside(coll1['features'], resolution=res)
boundarytools.utils.show_surface(allinside1)

share = (diff>0.05).sum() / (allinside1>0).sum() * 100 # count the full pixel where there is any diff/doubt
print('share of country that has any disagreement (>5% probability) across the two sources:', share, '%')

share = (diff>0.95).sum() / (allinside1>0).sum() * 100 # count only the highly doubtfull pixels
print('share of country that highly likely disagrees (>95% probability) across the two sources:', share, '%')



