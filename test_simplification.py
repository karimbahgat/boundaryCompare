
import shapefile
import shapely
from shapely.geometry import asShape

import numpy as np
import math

r = shapefile.Reader('gadm36_ALB_0.shp').shapes()
#r = shapefile.Reader(r"P:\(Temp Backup)\priocountries\priocountries.shp").shapes()[100:101]

def iterrings(geoj):
    if geoj['type'] == 'Polygon':
        for ring in geoj['coordinates']:
            yield ring
    elif geoj['type'] == 'MultiPolygon':
        for poly in geoj['coordinates']:
            for ring in poly:
                yield ring

def lineres(shapes):
    verts = 0
    circumf = 0
    for geoj in shapes:
        for ring in iterrings(geoj):
            verts += len(ring)
            geom = asShape({'type':'Polygon', 'coordinates':[ring]})
            circumf += geom.length
    print('--> verts={}, circumf={}'.format(verts, circumf))
    return circumf, verts, circumf / verts if verts else float('nan')

def linedists(shapes):
    dists = []
    for geoj in shapes:
        for ring in iterrings(geoj):
            ring = list(ring)
            if ring[0]!=ring[-1]: ring.append(ring[-1])
            for i in range(len(ring)-1):
                v1,v2 = ring[i:i+2]
                dx,dy = v1[0]-v2[0], v1[1]-v2[1]
                d = math.hypot(dx, dy)
                dists.append(d)
    return dists

shapes = [shape.__geo_interface__ for shape in r]
print('original lineres', lineres(shapes))
dists = linedists(shapes)
dmin = min(dists)
dmax = max(dists)
dmean = sum(dists) / len(dists)
print('original dist', dmin)

# simplify
import numpy as np
resdata = []
circdata = []
dmindata = []
dmaxdata = []
dmeandata = []
dmeddata = []
dquintdata = []
allshapes = []
alldists = []
for thresh in np.linspace(0, 0.1, 12): #[0, 0.0001, 0.001, 0.01, 0.1, 1]:
    print('threshold', thresh)
    # simplify
    _shapes = [asShape(shape).simplify(thresh, preserve_topology=False).__geo_interface__ for shape in shapes]
    allshapes.append((thresh,_shapes))
    # get new lineres
    circumf, verts, res = lineres(_shapes)
    # get dist min
    dists = linedists(_shapes)
    if dists:
        dmin = sorted(dists)[len(dists)//100] #min(dists)
        dmax = max(dists)
        dmean = sum(dists) / len(dists)
        dmed = sorted(dists)[len(dists)//2]
        dquint = sorted(dists)[len(dists)//4]
        print(dmin,dmax,dmean,dmed)
        dmindata.append((thresh,dmin))
        dmaxdata.append((thresh,dmax))
        dmeandata.append((thresh,dmean))
        dmeddata.append((thresh,dmed))
        dquintdata.append((thresh,dquint))
        alldists.append((thresh,dists))
    # compare
    print('-->', thresh, 'vs', res)
    print('-->', 'dist', dmin)
    ratio = res / thresh
    resdata.append((thresh,res))
    circdata.append((verts,circumf))

# maps?
import matplotlib.pyplot as plt
plt.clf()
fig,axes = plt.subplots(nrows=4, ncols=3)
axes = axes.flatten()
_prevshapes = []
for i,(thresh,_shapes) in enumerate(allshapes):
    ax = axes[i]
    ax.set_aspect('equal', 'datalim')
    # true/accurate previous shapes
    for geoj in _prevshapes:
        # main shape
        for ring in iterrings(geoj):
            ring = list(ring)
            if ring[0]!=ring[-1]: ring.append(ring[-1])
            x,y = zip(*ring)
            ax.plot(x, y, color='tab:red', marker='o')
    # existing/simplified shapes
    for geoj in _shapes:
        # main shape
        for ring in iterrings(geoj):
            ring = list(ring)
            if ring[0]!=ring[-1]: ring.append(ring[-1])
            x,y = zip(*ring)
            ax.plot(x, y, color='tab:blue', marker='o')
        # collect all rings as multilinestring
        lines = []
        for ring in iterrings(geoj):
            ring = list(ring)
            if ring[0]!=ring[-1]: ring.append(ring[-1])
            lines.append(ring)
        _geoj = {'type':'MultiLineString', 'coordinates':lines}
        # buffer the multilinestring
        buf = dmindata[i][1] #/2.0 # buffer by half of smallest vertex distance
        _geoj = asShape(_geoj).buffer(buf).__geo_interface__
        # draw buffer
        for ring in iterrings(_geoj):
            ring = list(ring)
            if ring[0]!=ring[-1]: ring.append(ring[-1])
            x,y = zip(*ring)
            ax.plot(x, y, color='black')
    _prevshapes = _shapes
    
fig.show()
hkjk

# histos
##import matplotlib.pyplot as plt
##plt.clf()
##fig,axes = plt.subplots(nrows=2, ncols=6)
##axes = axes.flatten()
##for i,(thresh,dists) in enumerate(alldists):
##    ax = axes[i]
##    ax.hist(dists)
##    ax.set_xlim(left=0)
##    #ax.set_title()
##fig.show()
##dsfs

# dist metrics graphs
import matplotlib.pyplot as plt
plt.clf()

x,y = zip(*dmindata)
plt.plot(x, y, marker='o', label='min')
x,y = zip(*dquintdata)
plt.plot(x, y, marker='o', label='quint')
x,y = zip(*dmeddata)
plt.plot(x, y, marker='o', label='median')
x,y = zip(*dmeandata)
plt.plot(x, y, marker='o', label='mean')
x,y = zip(*resdata)
plt.plot(x, y, marker='o', label='lineres?')
x,y = zip(*dmaxdata)
plt.plot(x, y, marker='o', label='max')

y = [_x for _x in x]
plt.plot(x, y, marker='o', color='black')

plt.legend()
plt.xlabel('simplification threshold')
plt.ylabel('distance min')
plt.show()
dsafas

# circumf
import matplotlib.pyplot as plt
x,y = zip(*circdata)
plt.plot(x, y)
plt.xlabel('simplification threshold')
plt.xlabel('vertices')
plt.ylabel('circumference')
plt.show()

# lineres
import matplotlib.pyplot as plt
x,y = zip(*resdata)
plt.plot(x, y)
plt.xlabel('simplification threshold')
plt.ylabel('avg line resolution')
plt.show()

# map
import pythongis as pg
pg.VectorData(rows=[[] for _ in range(len(shapes))], geometries=shapes).map().render().img.show()





