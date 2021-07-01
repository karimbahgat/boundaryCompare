
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

# calc line precision
print('line precision', bnd.line_resolution_min())

# set precision limit

# normal/gaussian decay
import numpy as np
def gaussian(x, mu, sig): # ie normal distribution
    # mu is the mean/median, sig is the standard deviation (sig**2 is the full variance/edge)
    # as equation: 1 / (sqrt(2*pi)*sig) * exp(-((x-mu)/sig)**2)/2)
    return 1./(np.sqrt(2.*np.pi)*sig)*np.exp(-np.power((x - mu)/sig, 2.)/2) / 100.0
mu = 0
sig = 0.18**2
bins = int((maxdist*2)//res)
x = [_x for _x in np.linspace(-maxdist, maxdist, bins)]
y = [gaussian(_x,mu,sig) for _x in np.linspace(-maxdist, maxdist, bins)]
print('sum gauss', sum(y))
import matplotlib.pyplot as plt
plt.plot(x, y)
plt.show()
import math
bnd.precision = '1 / (sqrt(2*pi)*{sig}) * exp((-((x-{mu})/{sig})**2)/2.0) / 100.0'.format(mu=mu, sig=sig)

# simple linear decay
#bnd.precision = '1 - x/{0}'.format(maxdist)

bnd.precision_range_max = maxdist
print('precision', bnd.precision)

#############################

# test distance
#surf = bnd.distance_surface(res, bbox, maxdist) #, False)
#bnd.show(surf=surf)

# test kernel
surf = bnd.precision_kernel(res, maxdist)
print(surf.shape)
boundarytools.utils.show_surface(surf)

# test precision surface
surf = bnd.precision_surface(res, bbox, maxdist)
bnd.show(surf=surf)

# final uncertainty surface
surf = bnd.uncertainty_surface(res, bbox, maxdist)
bnd.show(surf=surf)

#######################

# data 1
geom1 = shapefile.Reader(r"C:\Users\kimok\Desktop\boundary metric experiments\gadm36_ALB_0.shp").shape(0).__geo_interface__
bnd1 = boundarytools.uncertainty.Boundary(geom, 'x')

geom2 = shapefile.Reader(r"P:\(Temp Backup)\priocountries\priocountries.shp").shape(100).__geo_interface__
bnd2 = boundarytools.uncertainty.Boundary(geom, 'x')

# params
maxdist = 0.1
res = 0.01
bbox = bnd.bbox(maxdist)

# calc uncertainty
mu = 0
sig = 0.18**2
bnd1.precision = '1 / (sqrt(2*pi)*{sig}) * exp((-((x-{mu})/{sig})**2)/2.0) / 100.0'.format(mu=mu, sig=sig)
bnd2.precision = '1 / (sqrt(2*pi)*{sig}) * exp((-((x-{mu})/{sig})**2)/2.0) / 100.0'.format(mu=mu, sig=sig)

# create boundary
bnd = boundarytools.uncertainty.Boundary(geom, 'x')
bbox = bnd.bbox(maxdist)

surf1 = bnd.uncertainty_surface(res, bbox, maxdist)
bnd.show(surf=surf)

# equality test




