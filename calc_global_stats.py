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
import itertools

# params

OUTPUT_DIR = 'global_stats'
IGNORE_SOURCES = []
MAXPROCS = 3


def loop_country_levels():
    url = 'https://raw.githubusercontent.com/wmgeolab/geoContrast/stable/releaseData/geoContrast-meta.csv'
    raw = urlopen(url).read().decode('utf8')
    reader = csv.DictReader(raw.split('\n'))
    def key(row):
        return row['boundaryISO'], int(row['boundaryType'][-1])
    iso_levels = sorted(set([key(row) for row in reader]))
    for iso,level in iso_levels:
        yield iso,level


def get_country_level_stats(country, level):
    #results = {}

    # open areas
    try:
        path = 'global_relations/{}-ADM{}-areas.json'.format(iso, level)
        with open(path) as r:
            areas = json.loads(r.read())
    except:
        return None

    # open relations
    try:
        path = 'global_relations/{}-ADM{}-relations.json'.format(iso, level)
        with open(path) as r:
            relations = json.loads(r.read())
    except:
        return None

    # get all sources
    sources = set()
    for src,relations2 in relations.items():
        sources.add(src)
        for src2 in relations2.keys():
            sources.add(src2)

    # calc probability similar for each feature
    probabilities = {}
    for src,relations2 in relations.items():
        As = areas[src]
        probabilities_row = {}
        for src2,featurepairs in relations2.items():
            print('')
            print(src,src2)
            Bs = areas[src2]
            # probabilities for each feature
            featureprobs = feature_probabilities(As, Bs, featurepairs)
            #print('featureprobs',featureprobs)
            # get total source prob by taking probability OR weighted by share of area
            prob = 0
            Atot = sum(As)
            for A,fprob in zip(As, featureprobs):
                Aprob = A / Atot
                wprob = fprob * Aprob
                prob += wprob
            print('prob',prob)
            probabilities_row[src2] = prob
        probabilities[src] = probabilities_row

    # return dict of source pairs, each with a single probability/similarity metric
    return probabilities

def feature_probabilities(As, Bs, relations):
    # this function returns a list of probabilities for a particular source combination
    # each list entry is the probability that each feature is the same in the other source

    # create relations lookup dict
    key = lambda x: x[0] # group by row index
    relations_lookup = dict([(k,list(group)) for k,group in itertools.groupby(sorted(relations, key=key), key=key)])

    # calc probabilities
    probabilities = []
    for i,A in enumerate(As):
        related = relations_lookup.get(i, []) # if no related then prob = 0
        # calc total probability that feature A is in the other source
        prob = 0
        A = As[i] # could also be Adiff+AB
        for _,i2,(Adiff,Bdiff,AB) in related:
            AorB = sum([Adiff,Bdiff,AB])
            B = Bs[i2] # could also be Bdiff+AB
            if A == 0 or B == 0:
                # rare freak case of 0-area geoms
                continue
            equality = AB / AorB
            within = AB / A
            contains = AB / B
            pairprob = equality * within # ie probsame * probwithin
            prob += pairprob # probability OR

        probabilities.append(prob)
    
    return probabilities


def process(iso, level):
    # calc stats
    stats = get_country_level_stats(iso, level)
    if not stats:
        # relations havent been calculated, skip
        return

    # dump stats as json
    filename = '{}-ADM{}-stats.json'.format(iso, level)
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, 'w', encoding='utf8') as w:
        json.dump(stats, w, indent=4)

    # dump errors as json if any
    if 0: #errors:
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
        print('')
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
