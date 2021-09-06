# imports
import boundarytools
import numpy as np

import os
import sys
import json
from urllib.request import urlopen
import csv
import traceback
import multiprocessing as mp
import datetime
from time import time

# params

OUTPUT_DIR = 'global_stats'
IGNORE_SOURCES = []
MAXPROCS = 3

def get_country_level_stats(country, level):
    # first get all possible sources
    sourcedict = boundarytools.utils.find_geocontrast_sources(country, level)
    print('available sources:', sourcedict.keys())

    # next loop all pairs of sources
    errors = {}
    source_results_matrix = {}
    for source1,url1 in sourcedict.items():
        if source1 in IGNORE_SOURCES: continue
        if 'geoBoundaries' in source1:
            url1 = url1.replace('.topojson','.geojson')
            coll1 = boundarytools.utils.load_geojson_url(url1, load_shapely=True)
        else:
            coll1 = boundarytools.utils.load_topojson_url(url1, load_shapely=True)

        # simplify
        for feat in coll1['features']:
            feat['shapely'] = feat['shapely'].buffer(0).simplify(0.01)
        
        source_results_row = {}
        
        for source2,url2 in sourcedict.items():
            #if source2 == source1: continue
            if source2 in IGNORE_SOURCES: continue
            print('')
            print(source1, 'vs', source2)

            try:
                if 'geoBoundaries' in source2:
                    url2 = url2.replace('.topojson','.geojson')
                    coll2 = boundarytools.utils.load_geojson_url(url2, load_shapely=True)
                else:
                    coll2 = boundarytools.utils.load_topojson_url(url2, load_shapely=True)
                    
                # simplify
                for feat2 in coll2['features']:
                    feat2['shapely'] = feat2['shapely'].buffer(0).simplify(0.01)
                    
                # show
                #import matplotlib.pyplot as plt
                #boundarytools.utils.show_datasets(coll1, coll2)
                #plt.show()
                    
                # calc simil stats
                def similarity(feat1, feat2):
                    isec_area = feat1['shapely'].intersection(feat2['shapely']).area
                    union_area = feat1['shapely'].union(feat2['shapely']).area
                    equality = isec_area / union_area
                    within = isec_area / feat1['shapely'].area
                    contains = isec_area / feat2['shapely'].area
                    stats = {'equality':equality, 'within':within, 'contains':contains}
                    print(stats)
                    return stats
                feat1,feat2 = coll1['features'][0], coll2['features'][0]
                source_results_row[source2] = similarity(feat1, feat2)
                # first from persepctive of coll1
                #feat1,feat2 = coll1['features'][0], coll2['features'][0]
                #feat1['similarity'] = similarity(feat1, feat2)
                # then from perspective of coll2
                #feat2['similarity'] = similarity(feat2, feat1)
            except:
                err = traceback.format_exc()
                key = '{} VS {}'.format(source1,source2)
                errors[key] = err
            
        source_results_matrix[source1] = source_results_row

    return source_results_matrix, errors

def loop_country_levels():
    url = 'https://raw.githubusercontent.com/wmgeolab/geoContrast/main/releaseData/geoContrast-meta.csv'
    raw = urlopen(url).read().decode('utf8')
    reader = csv.DictReader(raw.split('\n'))
    def key(row):
        return row['boundaryISO'], int(row['boundaryType'][-1])
    iso_levels = sorted(set([key(row) for row in reader]))
    for iso,level in iso_levels:
        yield iso,level


def process(iso, level):
    # calc stats
    stats,errors = get_country_level_stats(iso, level)

    # dump stats as json
    filename = '{}-ADM{}-stats.json'.format(iso, level)
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, 'w', encoding='utf8') as w:
        json.dump(stats, w, indent=4)

    # dump errors as json if any
    if errors:
        filename = '{}-ADM{}-errors.json'.format(iso, level)
        path = os.path.join(OUTPUT_DIR, filename)
        with open(path, 'w', encoding='utf8') as w:
            w.write(json.dumps(errors, indent=4))


def process_logger(logfile, func, **kwargs):
    logger = open(logfile, 'w', encoding='utf8')
    sys.stdout = logger
    sys.stderr = logger
    print('PID:',os.getpid())
    print('time',datetime.datetime.now().isoformat())
    print('working path',os.path.abspath(''))
    # run it
    func(**kwargs)
    # finish
    print('finished!')
    print('time',datetime.datetime.now().isoformat())


if __name__ == '__main__':
    maxprocs = MAXPROCS
    procs = []

    # loop country levels
    for iso,level in loop_country_levels():
        print(iso,level)

        # skip if stats already exists
        filename = '{}-ADM{}-stats.json'.format(iso, level)
        path = os.path.join(OUTPUT_DIR, filename)
        if os.path.lexists(path):
            print('already exists, skipping')
            continue

        # local
        process(iso, level)
        continue

        # multiprocessing
        logfile = '{}-ADM{}-log.txt'.format(iso, level)
        logpath = os.path.join(OUTPUT_DIR, logfile)
        p = mp.Process(target=process_logger,
                       args=[logpath,process],
                       kwargs={'iso':iso, 'level':level})
        p.start()
        procs.append((p,time()))

        # Wait in line
        while len(procs) >= maxprocs:
            for p,t in procs:
                if not p.is_alive():
                    procs.remove((p,t))
                elif time()-t > 900:
                    p.terminate()
                    procs.remove((p,t))

    # waiting for last ones
    for p,t in procs:
        p.join()
