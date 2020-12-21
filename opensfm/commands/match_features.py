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
    name = 'match_features'
    help = 'Match features between image pairs'

    def add_arguments(self, parser):
        parser.add_argument('dataset', help='dataset to process')

    def run(self, args):

        # setup
        data = dataset.DataSet(args.dataset)
        images = data.images()
        exifs = {im: data.load_exif(im) for im in images}
        processes = data.config.get('processes', 1)
        start = time.time()

        #===== tag matching =====#
        
        # if a tag detection algorithm was used
        if data.config.get('use_apriltags',False) or data.config.get('use_arucotags',False) or data.config.get('use_chromatags',False):

            # all possible pairs
            pairs = match_candidates_all(images)

            all_pairs = {im: [] for im in images}
            for im1, im2 in pairs:
                all_pairs[im1].append(im2)
            logger.info('Matching tags in {} image pairs'.format(len(pairs)))

            # limit used detections
            ignore_tag_list = create_ignore_tag_list(data)
            print('Ignore Tag List: ')
            print(ignore_tag_list)

            # context
            ctx = Context()
            ctx.data = data
            ctx.ignore_tag_list = ignore_tag_list
            args = match_arguments(all_pairs, ctx)

            # run match
            if processes == 1:
                for arg in args:
                    match_tags(arg)
            else:
                p = Pool(processes)
                p.map(match_tags, args)
            
        #=== end tag matching ===#

        #===== feature matching =====#

        # setup pairs for matching
        pairs = match_candidates_all(images)
        logger.info('{} Initial matching image pairs'.format(len(pairs)))
        tag_pairs = set()
        meta_pairs = set()
        tag_prune_mode = data.config.get('prune_with_tags','none')

        # tag pairs
        if tag_prune_mode == 'strict' or tag_prune_mode == 'medium' or tag_prune_mode == 'loose':
            tag_pairs = match_candidates_from_tags(images, data)
            logger.info('{} Tag matching image pairs'.format(len(tag_pairs)))
        # no tag pairs, but still make tag graph for resectioning
        else:
            # build tag matches dictionary
            tag_matches = {}
            for im1 in images:
                try:
                    im1_tag_matches = data.load_tag_matches(im1)
                except IOError:
                    continue
                for im2 in im1_tag_matches:
                    tag_matches[im1, im2] = im1_tag_matches[im2]
            tags_graph = matching.create_tags_graph(tag_matches, data.config)
            data.save_tags_graph(tags_graph)

        # prune with metadata
        if data.config.get('prune_with_metadata',True):
            meta_pairs = match_candidates_from_metadata(images, exifs, data)
            logger.info('{} Meta matching image pairs'.format(len(meta_pairs)))
        if tag_pairs:
            pairs = pairs.intersection(tag_pairs)
        if meta_pairs:
            pairs = pairs.intersection(meta_pairs)
        logger.info('{} Final matching image pairs'.format(len(pairs)))

        # build pairs into dictionary
        final_pairs = {im: [] for im in images}
        for im1, im2 in pairs:
            final_pairs[im1].append(im2)

        # context
        ctx = Context()
        ctx.data = data
        ctx.cameras = ctx.data.load_camera_models()
        ctx.exifs = exifs
        ctx.p_pre, ctx.f_pre = load_preemptive_features(data)
        args = match_arguments(final_pairs, ctx)

        # match
        if processes == 1:
            for arg in args:
                match(arg)
        else:
            p = Pool(processes)
            p.map(match, args)
        #=== end feature matching ===#
        
        end = time.time()
        with open(ctx.data.profile_log(), 'a') as fout:
            fout.write('match_features: {0}\n'.format(end - start))


class Context:
    pass


def create_ignore_tag_list(data):
    
    # variables
    ignore_tag_list = []
    keep_ratio = data.config.get('ratio_tags_to_keep',1.0)
    
    # round ratio to 1% values (e.g. 0.009 becomes 0.01)
    keep_ratio = int(keep_ratio*100) / 100.0

    # load tag json and images
    tag_detections = data.load_tag_detection()

    # get unique ids set
    tag_ids = set()
    for image in tag_detections:
        dets = tag_detections[image]
        for det in dets:
            tag_ids.add(det.id)

    # get keep fraction  
    keep_fraction = Fraction(keep_ratio).limit_denominator()
    num_tags_to_keep = int(len(tag_ids) * keep_ratio)
    
    # add to ignore list
    n = 1
    for id in tag_ids:
        if n > keep_fraction.numerator:
            ignore_tag_list.append(id)
        if n == keep_fraction.denominator:
            n = 1
            continue
        n+=1

    # count number of detections per image after removing from ignore list
    detcounts = {}
    detsum = 0
    for image in tag_detections:
        detct = 0
        dets = tag_detections[image]
        for det in dets:
            if det.id not in ignore_tag_list:
                detct += 1
        detcounts[image] = detct
        detsum += detct

    # print
    logger.debug('Unique Tag IDs Found: '+str(len(tag_ids)))
    logger.debug('Keep Ratio: '+str(keep_ratio))
    logger.debug('Keep Fraction: '+str(keep_fraction.numerator)+' / '+str(keep_fraction.denominator))
    logger.debug('Number of Tags to Keep: '+str(len(tag_ids)-len(ignore_tag_list)))
    logger.debug('Number of Unique Tags per Image: '+str( (len(tag_ids)-len(ignore_tag_list)) / len(data.images() )))
    logger.debug('Number of total Tag Detections: '+str(detsum))
    logger.debug('Number of Tag Detections per Images: '+str( float(detsum) / len(data.images() ) ))
    
    # return
    return ignore_tag_list

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


def has_gps_info(exif):
    return (exif and
            'gps' in exif and
            'latitude' in exif['gps'] and
            'longitude' in exif['gps'])


def match_candidates_by_distance(images, exifs, reference, max_neighbors, max_distance):
    """Find candidate matching pairs by GPS distance."""
    if max_neighbors <= 0 and max_distance <= 0:
        return set()
    max_neighbors = max_neighbors or 99999999
    max_distance = max_distance or 99999999.
    k = min(len(images), max_neighbors + 1)

    points = np.zeros((len(images), 3))
    for i, image in enumerate(images):
        gps = exifs[image]['gps']
        points[i] = geo.topocentric_from_lla(
            gps['latitude'], gps['longitude'], gps['altitude'],
            reference['latitude'], reference['longitude'], reference['altitude'])

    tree = spatial.cKDTree(points)

    pairs = set()
    for i, image in enumerate(images):
        distances, neighbors = tree.query( points[i], k=k, distance_upper_bound=max_distance )
        for j in neighbors:
            if i != j and j < len(images):
                pairs.add(tuple(sorted((images[i], images[j]))))
    return pairs


def match_candidates_by_time(images, exifs, max_neighbors):
    """Find candidate matching pairs by time difference."""
    if max_neighbors <= 0:
        return set()
    k = min(len(images), max_neighbors + 1)

    times = np.zeros((len(images), 1))
    for i, image in enumerate(images):
        times[i] = exifs[image]['capture_time']

    tree = spatial.cKDTree(times)

    pairs = set()
    for i, image in enumerate(images):
        distances, neighbors = tree.query(times[i], k=k)
        for j in neighbors:
            if i != j and j < len(images):
                pairs.add(tuple(sorted((images[i], images[j]))))
    return pairs


def match_candidates_by_order(images, exifs, max_neighbors):
    """Find candidate matching pairs by sequence order."""
    if max_neighbors <= 0:
        return set()
    n = (max_neighbors + 1) / 2

    pairs = set()
    for i, image in enumerate(images):
        a = max(0, i - n)
        b = min(len(images), i + n)
        for j in range(a, b):
            if i != j:
                pairs.add( tuple( sorted( (images[i], images[j]) )))
    return pairs


def match_candidates_from_metadata(images, exifs, data):
    """Compute candidate matching pairs"""
    max_distance = data.config['matching_gps_distance']
    gps_neighbors = data.config['matching_gps_neighbors']
    time_neighbors = data.config['matching_time_neighbors']
    order_neighbors = data.config['matching_order_neighbors']
    if not data.reference_lla_exists():
        data.invent_reference_lla()
    reference = data.load_reference_lla()

    if not all(map(has_gps_info, exifs.values())):
        if gps_neighbors != 0:
            logger.warn("Not all images have GPS info. "
                        "Disabling matching_gps_neighbors.")
        gps_neighbors = 0
        max_distance = 0

    images.sort()

    d = match_candidates_by_distance(images, exifs, reference, gps_neighbors, max_distance)
    t = match_candidates_by_time(images, exifs, time_neighbors)
    o = match_candidates_by_order(images, exifs, order_neighbors)
    pairs = d | t | o

    res = {im: [] for im in images}
    for im1, im2 in pairs:
        res[im1].append(im2)
    return res

def match_candidates_from_tags(images,data):
    """Compute candidate matching pairs from tag connections"""

    # build tag matches dictionary
    tag_matches = {}
    for im1 in images:
        try:
            im1_tag_matches = data.load_tag_matches(im1)
        except IOError:
            continue
        for im2 in im1_tag_matches:
            tag_matches[im1, im2] = im1_tag_matches[im2]
    #print tag_matches
    tags_graph = matching.create_tags_graph(tag_matches, data.config)
    data.save_tags_graph(tags_graph)
    
    # create pairs  
    pairs = set()
    images_with_no_tags = []
    for i, im1 in enumerate(images):

        # get tags from tags_graph if they were detected for this image
        try:
            tags = tags_graph[im1]
        except:
            images_with_no_tags.append(im1)
            continue

        # for each tag seen in im1
        for tag in tags:
            matched_images = tags_graph[tag]

            # for each image connected to that tag
            for im2 in matched_images:
                
                # skip self connection
                if im1 == im2:
                    continue
                pairs.add( tuple( sorted( (im1,im2) )))

    # get tag prune mode
    tag_prune_mode = data.config.get('prune_with_tags','none')

    # add all possible matches for any image with no tag connections
    if tag_prune_mode == 'medium' or tag_prune_mode == 'loose':
        print('tag matching strictness at least medium.')

        for image in images_with_no_tags:
            for candidate in images:
                if image == candidate:
                    continue
                pairs.add( tuple( sorted(  (image,candidate) )))

    # merge separated components
    if tag_prune_mode == 'loose':
        print('tag matching strictness is loose.')

        # check for multiple connected components
        cc = sorted(nx.connected_components(tags_graph), key = len, reverse=True)
        if len(cc) > 1:

            # print
            print('Merging',len(cc),'tag graph connected components in loose mode:')

            # for each cc
            for cc_ct1 in range(0,len(cc)):
                for cc_ct2 in range(cc_ct1+1,len(cc)):
                    print('  Merging cc'+str(cc_ct1)+' with cc'+str(cc_ct2))

                    # pull out cc's
                    cc1 = cc[cc_ct1]
                    cc2 = cc[cc_ct2]

                    # for each node in cc1
                    for im1 in cc1:

                        # skip the tag nodes
                        if im1 not in images:
                            continue

                        # for each node in cc2
                        for im2 in cc2:

                            # skip the tag nodes
                            if im2 not in images:
                                continue

                            # add pair
                            #print 'adding pair: ',im1,' <==> ',im2
                            pairs.add( tuple( sorted( (im1,im2) )))

    # return pairs
    return pairs

def match_candidates_all(images):
    """All pairwise images are candidate matches"""
    
    # empty set
    pairs = set()
    
    # enumerate all possible pairs
    for i, image in enumerate(images):
        for j in range(i+1,len(images)):
            pairs.add( tuple( sorted( (images[i], images[j]) )))

    # store pairs as dictionary
    #res = {im: [] for im in images}
    #for im1, im2 in pairs:
    #    res[im1].append(im2)

    # return
    return pairs


def match_arguments(pairs, ctx):
    for i, (im, candidates) in enumerate(pairs.items()):
        yield im, candidates, i, len(pairs), ctx


def match_tags(args):
    """Compute all tag matches for a single image"""
    im1, candidates, i, n, ctx = args
    logger.info('Tag Matching {}  -  {} / {}'.format(im1, i + 1, n))
    ignore_tag_list = ctx.ignore_tag_list

    # tag matching
    if ctx.data.config.get('use_apriltags',False) or ctx.data.config.get('use_arucotags',False) or ctx.data.config.get('use_chromatags',False):

        # load features
        im1_tag_matches = {}
        try:
            p1, f1, i1, c1 = ctx.data.load_tag_features(im1)
        except:
            return
        
        # for each candidate image of im1
        for im2 in candidates:

            # try to load tag features for image
            try:
                p2, f2, i2, c2 = ctx.data.load_tag_features(im2)
            except:
                continue

            # store tag matches
            tag_matches = []

            # iterate image1 tag ids
            for id1 in range(0,p1.shape[0],4):

                # ignore if id in ignore_tag_list
                if f1[id1] in ignore_tag_list:
                    continue

                # iterate image2 tag ids
                for id2 in range(0,p2.shape[0],4):

                    # match found
                    if f1[id1] == f2[id2]:

                        # for each corner of that tag id
                        for i in range(0,4):

                            # add match point and tag id
                            tag_matches.append( [id1 + i, id2 + i, f1[id1]] )

            # matches for im1 to im2
            if tag_matches:
                im1_tag_matches[im2] = tag_matches

        # save tag matches
        if im1_tag_matches:
            #print im1_tag_matches
            ctx.data.save_tag_matches(im1, im1_tag_matches)

def match(args):
    """Compute all matches for a single image"""
    im1, candidates, i, n, ctx = args
    logger.info('Matching {}  -  {} / {}'.format(im1, i + 1, n))

    config = ctx.data.config
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
            matches_pre = matching.match_lowe_bf(ctx.f_pre[im1], ctx.f_pre[im2], config)
            config['lowes_ratio'] = lowes_ratio
            logger.debug("Preemptive matching {0}, time: {1}s".format(len(matches_pre), time.time() - t))
            if len(matches_pre) < preemptive_threshold:
                logger.debug("Discarding based of preemptive matches {0} < {1}".format(len(matches_pre), preemptive_threshold))
                continue

        # symmetric matching
        t = time.time()
        p1, f1, c1 = ctx.data.load_features(im1)
        i1 = ctx.data.load_feature_index(im1, f1)

        p2, f2, c2 = ctx.data.load_features(im2)
        i2 = ctx.data.load_feature_index(im2, f2)

        matches = matching.match_symmetric(f1, i1, f2, i2, config)
        logger.debug('{} - {} has {} candidate matches'.format(im1, im2, len(matches)))
        if len(matches) < robust_matching_min_match:
            im1_matches[im2] = []
            continue

        # robust matching
        t_robust_matching = time.time()
        camera1 = ctx.cameras[ctx.exifs[im1]['camera']]
        camera2 = ctx.cameras[ctx.exifs[im2]['camera']]

        rmatches = matching.robust_match(p1, p2, camera1, camera2, matches, config)

        if len(rmatches) < robust_matching_min_match:
            im1_matches[im2] = []
            continue
        im1_matches[im2] = rmatches
        
        logger.debug('Robust matching time : {0}s'.format( time.time() - t_robust_matching))

        logger.debug("Full matching {0} / {1}, time: {2}s".format( len(rmatches), len(matches), time.time() - t))
    ctx.data.save_matches(im1, im1_matches)