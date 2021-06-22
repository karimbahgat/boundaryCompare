
import boundarytools

import shapefile

# load data
geom = shapefile.Reader(r"C:\Users\kimok\Desktop\boundary metric experiments\gadm36_ALB_0.shp").shape(0).__geo_interface__
geom = shapefile.Reader(r"P:\(Temp Backup)\priocountries\priocountries.shp").shape(100).__geo_interface__

# params
maxdist = 0.1
res = 0.01

# create boundary
bnd = boundarytools.uncertainty.Boundary(geom, 'x')
bbox = bnd.bbox(maxdist)

# calc resolution
#maxdist = bnd.line_resolution_min()
bnd.precision = '1 - x/{0}'.format(maxdist)
bnd.precision_range_max = maxdist
print('precision', bnd.precision)

# test distance
surf = bnd.distance_surface(res, bbox, maxdist) #, False)
bnd.show(surf=surf)

# test kernel
surf = bnd.precision_kernel(res, maxdist)
boundarytools.utils.show_surface(surf)

# test precision surface
surf = bnd.precision_surface(res, bbox, maxdist)
bnd.show(surf=surf)

# final uncertainty surface
surf = bnd.uncertainty_surface(res, bbox, maxdist)
bnd.show(surf=surf)


