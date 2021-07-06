
# NOTE: it's possible the raster surfaces will be too computational/impractical
# so start with pure vector comparisons rather than raster ones
# ... 

from .uncertainty import _line_dists, _line_resolution_min

from .utils import iter_rings, bbox_union

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

def joint_probability_surface(*boundaries, resolution=None, bbox=None):
    if not bbox:
        bboxes = [b.uncertainty_bbox() for b in boundaries]
        bbox = bbox_union(*bboxes)
    if not resolution:
        dx = bbox[2]-bbox[0]
        dy = bbox[3]-bbox[1]
        import math
        diag = math.hypot(dx, dy)
        resolution = diag / 300.0

    import numpy as np
    joint = boundaries[0].uncertainty_surface(resolution, bbox)
    for b in boundaries[1:]:
        surf = b.uncertainty_surface(resolution, bbox)
        joint *= surf
    return joint

def disjoint_probability_surface(*boundaries, resolution=None, bbox=None):
    if not bbox:
        bboxes = [b.uncertainty_bbox() for b in boundaries]
        bbox = bbox_union(*bboxes)
    if not resolution:
        dx = bbox[2]-bbox[0]
        dy = bbox[3]-bbox[1]
        import math
        diag = math.hypot(dx, dy)
        resolution = diag / 300.0

    import numpy as np
    joint = 1 - boundaries[0].uncertainty_surface(resolution, bbox) # not
    for b in boundaries[1:]:
        surf = 1 - b.uncertainty_surface(resolution, bbox) # not
        joint *= surf
    return joint


    
