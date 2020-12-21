import logging
import time
import sys
import networkx as nx
from multiprocessing import Pool
from fractions import Fraction
import numpy as np
import scipy.spatial as spatial

from opensfm import dataset
from opensfm import geo
from opensfm import matching

logger = logging.getLogger(__name__)


class Command:
    name = 'match_reconstructions'
    help = 'Match features between image pairs from two reconstructions'

    def add_arguments(self, parser):
        parser.add_argument('dataset1', help='dataset1 with completed reconstruction to process')
        parser.add_argument('dataset2', help='dataset2 with completed reconstruction to process')

    def run(self, args):

        # setup
        # recon 1
        data1 = dataset.DataSet(args.dataset1)
        images1 = data1.images()
        exifs1 = {im: data1.load_exif(im) for im in images1}
        #recon 2
        data2 = dataset.DataSet(args.dataset2)
        images2 = data2.images()
        exifs2 = {im: data2.load_exif(im) for im in images2}
        # settings
        processes = data1.config.get('processes', 1)
        start = time.time()

        # setup pairs for matching
        pairs = match_candidates_all(images1, images2)
        logger.info('{} Initial matching image pairs'.format(len(pairs)))
        print(pairs)
        
        # context
        ctx = Context()
        ctx.data1 = data1
        ctx.data2 = data2
        ctx.cameras1 = ctx.data1.load_camera_models()
        ctx.cameras2 = ctx.data2.load_camera_models()
        ctx.exifs1 = exifs1
        ctx.exifs2 = exifs2
        ctx.p_pre1, ctx.f_pre1 = load_preemptive_features(data1)
        ctx.p_pre2, ctx.f_pre2 = load_preemptive_features(data2)
        args = match_arguments(pairs, ctx)

        # match
        if processes == 1:
            for arg in args:
                match(arg)
        else:
            p = Pool(processes)
            p.map(match, args)
        #=== end feature matching ===#
        
        end = time.time()
        with open(ctx.data1.profile_log(), 'a') as fout:
            fout.write('match_reconstructions: {0}\n'.format(end - start))
        with open(ctx.data2.profile_log(), 'a') as fout:
            fout.write('match_reconstructions: {0}\n'.format(end - start))


class Context:
    pass

def load_preemptive_features(data):
    p, f = {}, {}
    if data.config['preemptive_threshold'] > 0:
        logger.debug('Loading preemptive data')
        for image in data.images():
            try:
                p[image], f[image] = \
                    data.load_preemtive_features(image)
            except IOError:
                p, f, c = data.load_features(image)
                p[image], f[image] = p, f
            preemptive_max = min(data.config.get('preemptive_max', p[image].shape[0]), p[image].shape[0])
            p[image] = p[image][:preemptive_max, :]
            f[image] = f[image][:preemptive_max, :]
    return p, f

def match_candidates_all(images1, images2):
    """All pairwise images are candidate matches"""
    
    # empty set
    pairs = set()
    
    # enumerate all possible pairs
    for im1 in images1:
        for im2 in images2:
            pairs.add( tuple( (im1, im2) ) )
    #print(pairs)
    
    #for i, image in enumerate(images):
    #    for j in range(i+1,len(images)):
    #        pairs.add( tuple( sorted( (images[i], images[j]) )))

    # store pairs as dictionary
    res = {im: [] for im in images1}
    for im1, im2 in pairs:
        res[im1].append(im2)

    # return
    return res


def match_arguments(pairs, ctx):
    for i, (im, candidates) in enumerate(pairs.items()):
        yield im, candidates, i, len(pairs), ctx

def match(args):
    """Compute all matches for a single image"""
    im1, candidates, i, n, ctx = args
    logger.info('Matching {}  -  {} / {}'.format(im1, i + 1, n))

    config = ctx.data1.config
    robust_matching_min_match = config['robust_matching_min_match']
    preemptive_threshold = config['preemptive_threshold']
    lowes_ratio = config['lowes_ratio']
    preemptive_lowes_ratio = config['preemptive_lowes_ratio']

    im1_matches = {}

    for im2 in candidates:
        # preemptive matching
        if preemptive_threshold > 0:
            t = time.time()
            config['lowes_ratio'] = preemptive_lowes_ratio
            matches_pre = matching.match_lowe_bf(ctx.f_pre1[im1], ctx.f_pre2[im2], config)
            config['lowes_ratio'] = lowes_ratio
            logger.debug("Preemptive matching {0}, time: {1}s".format(len(matches_pre), time.time() - t))
            if len(matches_pre) < preemptive_threshold:
                logger.debug("Discarding based of preemptive matches {0} < {1}".format(len(matches_pre), preemptive_threshold))
                continue

        # symmetric matching
        t = time.time()
        p1, f1, c1 = ctx.data1.load_features(im1)
        i1 = ctx.data1.load_feature_index(im1, f1)

        p2, f2, c2 = ctx.data2.load_features(im2)
        i2 = ctx.data2.load_feature_index(im2, f2)

        matches = matching.match_symmetric(f1, i1, f2, i2, config)
        logger.debug('{} - {} has {} candidate matches'.format(im1, im2, len(matches)))
        if len(matches) < robust_matching_min_match:
            im1_matches[im2] = []
            continue

        # robust matching
        t_robust_matching = time.time()
        camera1 = ctx.cameras1[ctx.exifs1[im1]['camera']]
        camera2 = ctx.cameras2[ctx.exifs2[im2]['camera']]

        rmatches = matching.robust_match(p1, p2, camera1, camera2, matches, config)

        if len(rmatches) < robust_matching_min_match:
            im1_matches[im2] = []
            continue
        im1_matches[im2] = rmatches
        
        logger.debug('Robust matching time : {0}s'.format( time.time() - t_robust_matching))

        logger.debug("Full matching {0} / {1}, time: {2}s".format( len(rmatches), len(matches), time.time() - t))
    ctx.data1.save_other_recon_matches(im1, im1_matches)
    ctx.data1.save_matches(im1, im1_matches)