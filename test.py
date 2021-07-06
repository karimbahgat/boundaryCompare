
import boundarytools

import shapefile

if 0:
    # load data
    geom = shapefile.Reader(r"C:\Users\kimok\Desktop\boundary metric experiments\gadm36_ALB_1.shp").shape(0).__geo_interface__
##    r = shapefile.Reader(r"P:\(Temp Backup)\priocountries\priocountries.shp")
##    for i,row in enumerate(r.iterRecords()):
##        if row['GEOUNIT'] == 'Albania':
##            geom = r.shape(i).__geo_interface__

    # params
    #maxdist = 0.1
    #res = 0.005

    # create boundary
    bnd = boundarytools.uncertainty.Boundary(geom, 'x')
    meddist = bnd.line_resolution_med()
    maxdist = meddist * 3 # if the median line resolution = std of the normal distribution, then 3x std = full range
    bnd.precision_range_max = maxdist
    res = maxdist / 10.0 # how many pixels to fit within the range
    #bbox = bnd.bbox(maxdist)

    # calc line precision
    print('line precision', meddist)

    # set precision limit

    # normal/gaussian decay, take 1 (works?)
##    import numpy as np
##    def gaussian(x, mu, sig): # ie normal distribution
##        # mu is the mean/median, sig is the standard deviation (sig**2 is the full variance/edge)
##        # as equation: 1 / (sqrt(2*pi)*sig) * exp(-((x-mu)/sig)**2)/2)
##        return 1./(np.sqrt(2.*np.pi)*sig)*np.exp(-np.power((x - mu)/sig, 2.)/2) / 100.0
##    mu = 0
##    sig = meddist #0.18**2
##    bins = int((maxdist*2)//res)
##    x = [_x for _x in np.linspace(-maxdist, maxdist, bins)]
##    y = [gaussian(_x,mu,sig) for _x in x]

    # normal/gaussian decay, take 2 (experimental)
    import numpy as np
    def normpdf(x, mean, sd):
        var = sd**2
        denom = (2*np.pi*var)**.5
        num = np.exp(-(x-mean)**2/(2*var))
        return num/denom
    mu = 0
    sig = meddist #0.18**2
    bins = int((maxdist*2)//res)
    x = np.linspace(-maxdist, maxdist, bins)
    y = normpdf(x, mu, sig)
    print('sum gauss', sum(y))

    # plot normal distr
    import matplotlib.pyplot as plt
    plt.plot(x, y)
    plt.show()
    import math
    bnd.precision = '1 / (sqrt(2*pi)*{sig}) * exp((-((x-{mu})/{sig})**2)/2.0) / 100.0'.format(mu=mu, sig=sig)

    # simple linear decay
    #bnd.precision = '1 - x/{0}'.format(maxdist)

    #bnd.precision_range_max = maxdist
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
    surf = bnd.precision_surface(res) #, bbox, maxdist)
    bnd.show(surf=surf)

    # final uncertainty surface
    surf = bnd.uncertainty_surface(res) #, bbox, maxdist)
    bnd.show(surf=surf)

#######################

print('\nCOMPARISONS')

def compare(geom1, geom2):
    # params
    # ... 
    
    # data 1
    bnd1 = boundarytools.uncertainty.NormalBoundary(geom1)
    res = bnd1.precision_range_max / 10.0
    print(bnd1.precision, bnd1.precision_range_max, res)
    bnd1.show(bnd1.uncertainty_surface(res))

    # data 2
    bnd2 = boundarytools.uncertainty.NormalBoundary(geom2)
    res = bnd2.precision_range_max / 10.0
    print(bnd2.precision, bnd2.precision_range_max, res)
    bnd2.show(bnd2.uncertainty_surface(res))

    # show overlap
    surf1,surf2,overlap = bnd1.overlap_surface(bnd2)
    bnd1.show(surf=overlap)

    # show difference
    surf1,surf2,diff = bnd1.difference_surface(bnd2)
    bnd1.show(surf=diff)

    # stats test
    stats = bnd1.similarity(bnd2)
    print(stats)

# compare country from different sources
geom1 = shapefile.Reader(r"C:\Users\kimok\Desktop\boundary metric experiments\gadm36_ALB_0.shp").shape(0).__geo_interface__
for feat in shapefile.Reader(r"P:\(Temp Backup)\priocountries\priocountries.shp").iterShapeRecords():
    if feat.record['GEOUNIT'] == 'Albania':
        geom2 = feat.shape.__geo_interface__
compare(geom1, geom2)

# compare adm1 with parent adm0
geom1 = shapefile.Reader(r"C:\Users\kimok\Desktop\boundary metric experiments\gadm36_ALB_0.shp").shape(0).__geo_interface__
geom2 = shapefile.Reader(r"C:\Users\kimok\Desktop\boundary metric experiments\gadm36_ALB_1.shp").shape(0).__geo_interface__
compare(geom1, geom2)

# compare adm0 with child adm1
compare(geom2, geom1)

# compare shared?
# ... 



