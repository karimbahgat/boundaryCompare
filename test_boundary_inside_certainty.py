
import boundarytools
import numpy as np

import json
from urllib.request import urlopen

# params
SIGNED = False

# setup data
country = 'CHE'

topoj = json.loads(urlopen('https://media.githubusercontent.com/media/wmgeolab/geoContrast/main/releaseData/naturalEarth/{country}/ADM1/naturalEarth-{country}-ADM1.topojson'.format(country=country)).read())
coll1 = boundarytools.utils.topo2geoj(topoj)

topoj = json.loads(urlopen('https://media.githubusercontent.com/media/wmgeolab/geoContrast/main/releaseData/gadm/{country}/ADM1/gadm-{country}-ADM1.topojson'.format(country=country)).read())
coll2 = boundarytools.utils.topo2geoj(topoj)

##topoj = json.loads(urlopen('https://media.githubusercontent.com/media/wmgeolab/geoContrast/main/releaseData/CIV_CNTIG/{country}/ADM1/CIV_CNTIG-{country}-ADM1.topojson'.format(country=country)).read())
##coll3 = boundarytools.utils.topo2geoj(topoj)

#feat1,feat2 = feat2,feat1 # see if switching has an effect

def compare_multi(feats):
    boundaries = [boundarytools.uncertainty.NormalBoundary(feat['geometry']) for feat in feats]

    # resolution
    res = min(bnd.precision_range_max for bnd in boundaries) / 2.0
    print('resolution', res)

    # get bboxes
    bboxes = [b.uncertainty_bbox() for b in boundaries]
    bbox = boundarytools.utils.bbox_union(*bboxes)

    # gen edge surfaces
##    for b in boundaries:
##        #surf = b.precision_surface(resolution=res, bbox=bbox)
##        #b.show(surf)
##        
##        inside = b.uncertainty_surface(res, bbox=bbox)
##        b.show(inside, bbox=bbox)
##
##        outside = 1 - inside
##        b.show(outside, bbox=bbox)
##
##        both = inside * outside #np.maximum(inside, outside) # ie probability that A says
##        b.show(both, bbox=bbox)
##
##        none = 1 - both
##        b.show(none, bbox=bbox)

    # precalc
    print('precalc')
    for bnd in boundaries:
        bnd._inside = bnd.uncertainty_surface(res, bbox=bbox)
        bnd._outside = 1 - bnd._inside
    # get cumulative or, ie that any of the sources disagree
    print('cumul')
    cumul = bnd._inside * 0 # null
    prev = boundaries[0]
    for bnd in boundaries[1:]:
        # if (Ainside and Boutside) or (Aoutside or Binside) # ie that both sources disagree on either inside or outside
        inside_outside = (bnd._inside * prev._outside)
        outside_inside = (bnd._outside * prev._inside)
        disagree = inside_outside + outside_inside - (inside_outside * outside_inside)
        cumul += disagree - (cumul * disagree)
    # show
    boundarytools.utils.show_boundaries(boundaries, cumul, bbox=bbox)
            
#compare_multi([feat1,feat2,feat3])

#################

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

    boundarytools.utils.show_boundaries(boundaries, cumul, bbox=bbox)
    return cumul

# boundaries
boundaries1 = [boundarytools.uncertainty.NormalBoundary(feat['geometry']) for feat in coll1['features']]
boundaries2 = [boundarytools.uncertainty.NormalBoundary(feat['geometry']) for feat in coll2['features']]

# resolution
res1 = min(bnd.precision_range_max for bnd in boundaries1) / 2.0
res2 = min(bnd.precision_range_max for bnd in boundaries2) / 2.0
print(res1,res2)
res = min(res1,res2)
res = 0.01
print('resolution', res)

# get bboxes
bboxes = [b.uncertainty_bbox() for b in boundaries1] + [b.uncertainty_bbox() for b in boundaries2]
bbox = boundarytools.utils.bbox_union(*bboxes)
        
source1 = probability_inside(coll1['features'], resolution=res, bbox=bbox)
source2 = probability_inside(coll2['features'], resolution=res, bbox=bbox)

both = source1 * source2
boundarytools.utils.show_surface(both)

# CONCLUSIONS:
# this works but doesnt really talk about disagreement
# but rather the degree of certainty that you are fully within one boundary and not another, ie away from edge zone
# combining multiple sources i guess just says if on randomly picked one of the datasets on top of it




