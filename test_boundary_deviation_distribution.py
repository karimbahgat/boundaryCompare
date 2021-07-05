
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
    #if f['properties']['name'] == 'Denguélé':
    #if f['properties']['name'] == 'Savanes':
    if f['properties']['name'] == 'Zanzan':
        feat1 = f
        break

topoj = json.loads(urlopen('https://media.githubusercontent.com/media/wmgeolab/geoContrast/main/releaseData/gadm/{country}/ADM1/gadm-{country}-ADM1.topojson'.format(country=country)).read())
coll2 = boundarytools.utils.topo2geoj(topoj)
for f in coll2['features']:
    #if f['properties']['NAME_1'] == 'Denguélé':
    #if f['properties']['NAME_1'] == 'Savanes':
    if f['properties']['NAME_1'] == 'Zanzan':
        feat2 = f
        break

#feat1,feat2 = feat2,feat1 # see if switching has an effect

assert feat1 and feat2

# show
d1 = {'type': 'FeatureCollection', 'features': [feat1]}
d2 = {'type': 'FeatureCollection', 'features': [feat2]}
#boundarytools.utils.show_datasets(d1, d2)

# calc dists
dists = boundarytools.compare.boundary_distances(feat1['geometry'], feat2['geometry'], 0.01, signed_distances=SIGNED)
dists = np.array(dists)
print('distances', len(dists))

# fake the distribution to be +- around assumed mean of 0
if not SIGNED:
    dists = np.append(dists, -dists)

# plot distribution
import matplotlib.pyplot as plt
ys,bins,patches = plt.hist(dists, bins=100, density=True, label='true distances') #, cumulative=True) #, range=(0,2e-09))
xs = bins[:-1] # use only start of each bin as x value
#plt.xscale('log')

# add in normal dist (non-scipy)
import math
def normpdf(x, mean, sd):
    var = float(sd)**2
    denom = (2*math.pi*var)**.5
    num = math.exp(-(float(x)-float(mean))**2/(2*var))
    return num/denom
mean = dists.mean() # since we ignore the sign of the distances this should be around 0
std = dists.std()
ypred = [normpdf(x, mean, std) for x in xs]
plt.plot(xs, ypred, label='true normal distribution')

# add in normal dist (scipy)
##from scipy.stats import norm
##mu,std = norm.fit(dists)
##ypred = norm.pdf(xs, mu, std)
##plt.plot(xs, ypred)

# add in est. normal dist based on boundary line resolution metrics

# HOWEVER, THIS MIGHT BE THE WRONG WAY TO USE IT? 
# THIS SHOULD ONLY BE ABOUT COMPARING TWO BOUNDARIES AND ESTIMATING PROBABILITIES OF BEING EQUAL? 

# min line res
##res1 = boundarytools.uncertainty.Boundary(feat1['geometry'], '').precision_range_max
##res2 = boundarytools.uncertainty.Boundary(feat2['geometry'], '').precision_range_max
##res = max(res1,res2)
##mean = 0
##std = res1 #/ 3.0  normal line distribution
##ypred = [normpdf(x, mean, std) for x in xs]
##plt.plot(xs, ypred, label='est. normal distribution (min line res.)')

# median line res
res1 = np.median( np.array(boundarytools.uncertainty._line_dists([feat1['geometry']])) )
res2 = np.median( np.array(boundarytools.uncertainty._line_dists([feat2['geometry']])) )
res = max(res1,res2)
mean = 0

std = res #/ 3.0  normal line distribution
ypred = [normpdf(x, mean, std) for x in xs]
plt.plot(xs, ypred, label='est. normal distribution (median line res.)')

##std = res1 #/ 3.0  normal line distribution
##ypred = [normpdf(x, mean, std) for x in xs]
##plt.plot(xs, ypred, label='est. normal distribution 1 (median line res.)')
##
##std = res2 #/ 3.0  normal line distribution
##ypred = [normpdf(x, mean, std) for x in xs]
##plt.plot(xs, ypred, label='est. normal distribution 2 (median line res.)')

# mean line res
res1 = np.array(boundarytools.uncertainty._line_dists([feat1['geometry']])).mean()
res2 = np.array(boundarytools.uncertainty._line_dists([feat2['geometry']])).mean()
res = max(res1,res2)
mean = 0

std = res #/ 3.0  normal line distribution
ypred = [normpdf(x, mean, std) for x in xs]
plt.plot(xs, ypred, label='est. normal distribution (mean line res.)')

##std = res1 #/ 3.0  normal line distribution
##ypred = [normpdf(x, mean, std) for x in xs]
##plt.plot(xs, ypred, label='est. normal distribution 1 (mean line res.)')
##
##std = res2 #/ 3.0  normal line distribution
##ypred = [normpdf(x, mean, std) for x in xs]
##plt.plot(xs, ypred, label='est. normal distribution 2 (mean line res.)')

# show
plt.legend()
plt.show()

# CONCLUSION
# the idea here is something like:
# here we are comparing two sets of boundaries, one of which is higher resolution than the other
# if we arbitrarily decide that the finer resolution is the "truth"
# then calculating their distances will yield a distribution, which generally appears to follow a normal distribution
# the idea is to see which resolution metric more closely is able to reflect the true normal distribution
# turns out this is the median vertex line resolution, followed by the mean in second place
#
# but this was when assuming the other dataset was the truth
# but we will never really know where the true boundary is, nor should it matter
# what does matter is that we use information from the boundary structure itself as a useful indicator for the range
# and distribution of the probability of where the boundary is located
# for more coarsely defined boundaries the median resolution will be large and thus a larger error margin (less specific)
# uncertainty estimate, while more finely defined boundaries will have smaller median resolutions and thus a smaller
# (more specific) uncertainty estimate.
# ie all it means is that better/finer data gives us a more precise range of where the boundary might be.
# in short, given the median vertex line resolution, we can give an estimate of where the true boundary is likely to be

# try showing boundary surface now
res1 = np.median( np.array(boundarytools.uncertainty._line_dists([feat1['geometry']])) )
print('boundary 1, res', res1)
precision = '1 / (sqrt(2*pi)*{sig}) * exp((-((x-{mu})/{sig})**2)/2.0) / 100.0'.format(mu=mean, sig=res1)
bnd = boundarytools.uncertainty.Boundary(feat1['geometry'], precision, precision_range_max=res1*3)
surf = bnd.uncertainty_surface(res1)
bnd.show(surf=surf)

res2 = np.median( np.array(boundarytools.uncertainty._line_dists([feat2['geometry']])) )
print('boundary 2, res', res2)
precision = '1 / (sqrt(2*pi)*{sig}) * exp((-((x-{mu})/{sig})**2)/2.0) / 100.0'.format(mu=mean, sig=res2)
bnd = boundarytools.uncertainty.Boundary(feat2['geometry'], precision, precision_range_max=res2*3)
surf = bnd.uncertainty_surface(res2)
bnd.show(surf=surf)

