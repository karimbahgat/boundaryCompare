
# NOTE: it's possible the raster surfaces will be too computational/impractical
# so start with pure vector comparisons rather than raster ones
# ... 

from .uncertainty import _line_dists, _line_resolution_min

from .utils import iter_rings

import shapely
from shapely.geometry import asShape, LineString, MultiLineString

def boundary_distances(geom1, geom2, interval_dist=None, signed_distances=False):
    # signed_distances is whether to consider the sign of the distances in terms of distance inside (negative)
    # ...and outside (positive) geom2. More computationally costly. 

    # determine min line resolution
    if not interval_dist:
        dists = _line_dists([geom1])
        res1 = _line_resolution_min(dists)
        dists = _line_dists([geom2])
        res2 = _line_resolution_min(dists)
        interval_dist = min(res1, res2)
        print('interval dist set to min res', interval_dist)

    # create shapely geoms
    if signed_distances:
        inside = asShape(geom2)
    rings = list(iter_rings(geom2))
    shp2 = MultiLineString(rings)

    # walk and sample points along boundary of geom1
    dists = []
    for ring in iter_rings(geom1):
        shp1 = LineString(ring)
        perim = shp1.length
        pos = 0
        while pos < perim:
            sample = shp1.interpolate(pos)
            dist = sample.distance(shp2)
            if signed_distances:
                _,nearest = shapely.ops.nearest_points(sample, inside)
                if nearest.intersects(inside):
                    dist *= -1
            dists.append(dist)
            pos += interval_dist

    return dists



    
