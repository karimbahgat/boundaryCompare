import numpy as np

def iter_rings(geoj):
    '''Iterates through all rings of a polygon/multipolygon
    '''
    if geoj['type'] == 'Polygon':
        for ring in geoj['coordinates']:
            yield ring
    elif geoj['type'] == 'MultiPolygon':
        for poly in geoj['coordinates']:
            for ring in poly:
                yield ring

def topo2geoj(data):
    '''Data is the toplevel topojson dict containing: type, objects, arcs'''
    from topojson.utils import geometry
    lyr = list(data['objects'].keys())[0]
    tfeatures = data['objects'][lyr]['geometries']
    data['arcs'] = [np.array(arc) for arc in data['arcs']] # topojson.utils.geometry() assumes np arrays
    geoj = {'type': "FeatureCollection", 'features': []}
    for tfeat in tfeatures:
        #print(tfeat['type'], tfeat['properties']) #, tfeat['arcs']) 
        feat = {'type': "Feature"}
        feat['properties'] = tfeat['properties'].copy()
        feat['geometry'] = geometry(tfeat, data['arcs'], data.get('transform'))
        geoj['features'].append(feat)
    return geoj

def morphology(arr, kernel, op, dtype):
    count = 0
    output = np.zeros(arr.shape, dtype=dtype)
    # should be much faster... 
    kernel_half = (kernel.shape[0] - 1) // 2
    for ky in range(kernel.shape[0]):
        ky_offset = kernel_half - ky
        y1 = max(ky_offset, 0)
        y2 = min(arr.shape[0]+ky_offset, arr.shape[0])
        #oy1 = max(ky, 0)
        #oy2 = min(ky+(y2-y1), output.shape[0])
        for kx in range(kernel.shape[1]):
            kx_offset = kernel_half - kx
            x1 = max(kx_offset, 0)
            x2 = min(arr.shape[1]+kx_offset, arr.shape[1])

            kval = kernel[ky,kx]
            kval_extract = kval * arr[y1:y2, x1:x2]

            slices = slice(ky,kval_extract.shape[0]), slice(kx,kval_extract.shape[1])
            #print(slices,output[slices].shape)
            output[slices] = op([output[slices], kval_extract[slices]])
    count = output.sum()
    return count,output

def burn(val, geometry, drawer, transform):
    from PIL import ImagePath
    geotype = geometry["type"]

    # set the coordspace to vectordata bbox
    a,b,c,d,e,f = transform

    # if fill val is None, then draw binary outline
    fill = val
    outline = 255 if val is None else None
    holefill = 0 if val is not None else None
    holeoutline = 255 if val is None else None
    #print ["burnmain",fill,outline,"burnhole",holefill,holeoutline]

    # make all multis so can treat all same
    coords = geometry["coordinates"]
    if not "Multi" in geotype:
        coords = [coords]

    # polygon, basic black fill, no outline
    if "Polygon" in geotype:
        for poly in coords:
            # exterior
            exterior = [tuple(p) for p in poly[0]]
            path = ImagePath.Path(exterior)
            #print list(path)[:10]
            path.transform((a,b,c,d,e,f))
            #print list(path)[:10]
            drawer.polygon(path, fill=fill, outline=outline)
            # holes
            if len(poly) > 1:
                for hole in poly[1:]:
                    hole = [tuple(p) for p in hole]
                    path = ImagePath.Path(hole)
                    path.transform((a,b,c,d,e,f))
                    drawer.polygon(path, fill=holefill, outline=holeoutline)
                    
    # line, 1 pixel line thickness
    elif "LineString" in geotype:
        for line in coords:
            line = [tuple(p) for p in line]
            path = ImagePath.Path(line)
            path.transform((a,b,c,d,e,f))
            drawer.line(path, fill=outline)
        
    # point, 1 pixel square size
    elif "Point" in geotype:
        for p in coords:
            p = tuple(p)
            path = ImagePath.Path([p])
            path.transform((a,b,c,d,e,f))
            drawer.point(path, fill=outline)

def show_surface(surf):
    import matplotlib.pyplot as plt
    plt.imshow(surf)
    plt.show()

def show_datasets(data1, data2):
    import matplotlib.pyplot as plt
    from shapely.geometry import asShape
    # setup plot
    plt.clf()
    ax = plt.gca()
    ax.set_aspect('equal', 'datalim')
    # data1
    for feat in data1['features']:
        for ring in iter_rings(feat['geometry']):
            ring = list(ring)
            if ring[0]!=ring[-1]: ring.append(ring[-1])
            x,y = zip(*ring)
            plt.plot(x, y, color='tab:blue', marker='')
    # data2
    for feat in data2['features']:
        for ring in iter_rings(feat['geometry']):
            ring = list(ring)
            if ring[0]!=ring[-1]: ring.append(ring[-1])
            x,y = zip(*ring)
            plt.plot(x, y, color='tab:red', marker='')
    plt.show()
