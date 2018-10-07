import numpy as np
import cv2
import pyopengv
import networkx as nx
import logging
import sys
import math
from collections import defaultdict
from itertools import combinations

from opensfm import context
from opensfm import types
from opensfm.unionfind import UnionFind


logger = logging.getLogger(__name__)


# pairwise matches
def match_lowe(index, f2, config):
    search_params = dict(checks=config.get('flann_checks', 200))
    results, dists = index.knnSearch(f2, 2, params=search_params)
    squared_ratio = config.get('lowes_ratio', 0.6)**2  # Flann returns squared L2 distances
    good = dists[:, 0] < squared_ratio * dists[:, 1]
    matches = zip(results[good, 0], good.nonzero()[0])
    return np.array(matches, dtype=int)


def match_symmetric(fi, indexi, fj, indexj, config):
    if config.get('matcher_type', 'FLANN') == 'FLANN':
        matches_ij = [(a,b) for a,b in match_lowe(indexi, fj, config)]
        matches_ji = [(b,a) for a,b in match_lowe(indexj, fi, config)]
    else:
        matches_ij = [(a,b) for a,b in match_lowe_bf(fi, fj, config)]
        matches_ji = [(b,a) for a,b in match_lowe_bf(fj, fi, config)]

    matches = set(matches_ij).intersection(set(matches_ji))
    return np.array(list(matches), dtype=int)


def convert_matches_to_vector(matches):
    '''Convert Dmatch object to matrix form
    '''
    matches_vector = np.zeros((len(matches),2),dtype=np.int)
    k = 0
    for mm in matches:
        matches_vector[k,0] = mm.queryIdx
        matches_vector[k,1] = mm.trainIdx
        k = k+1
    return matches_vector


def match_lowe_bf(f1, f2, config):
    '''Bruteforce feature matching
    '''
    assert(f1.dtype.type==f2.dtype.type)
    if (f1.dtype.type == np.uint8):
        matcher_type = 'BruteForce-Hamming'
    else:
        matcher_type = 'BruteForce'
    matcher = cv2.DescriptorMatcher_create(matcher_type)
    matches = matcher.knnMatch(f1, f2, k=2)

    ratio = config.get('lowes_ratio', 0.6)
    good_matches = []
    for match in matches:
        if match and len(match) == 2:
            m, n = match
            if m.distance < ratio * n.distance:
                good_matches.append(m)
    good_matches = convert_matches_to_vector(good_matches)
    return np.array(good_matches, dtype=int)


def robust_match_fundamental(p1, p2, matches, config):
    '''Computes robust matches by estimating the Fundamental matrix via RANSAC.
    '''
    if len(matches) < 8:
        return np.array([])

    p1 = p1[matches[:, 0]][:, :2].copy()
    p2 = p2[matches[:, 1]][:, :2].copy()

    FM_RANSAC = cv2.FM_RANSAC if context.OPENCV3 else cv2.cv.CV_FM_RANSAC
    F, mask = cv2.findFundamentalMat(p1, p2, FM_RANSAC, config.get('robust_matching_threshold', 0.006), 0.9999)
    inliers = mask.ravel().nonzero()

    if F[2,2] == 0.0:
        return []

    return matches[inliers]


def compute_inliers_bearings(b1, b2, T):
    R = T[:, :3]
    t = T[:, 3]
    p = pyopengv.triangulation_triangulate(b1, b2, t, R)

    br1 = p.copy()
    br1 /= np.linalg.norm(br1, axis=1)[:, np.newaxis]

    br2 = R.T.dot((p - t).T).T
    br2 /= np.linalg.norm(br2, axis=1)[:, np.newaxis]

    ok1 = np.linalg.norm(br1 - b1, axis=1) < 0.01   # TODO(pau): compute angular error and use proper threshold
    ok2 = np.linalg.norm(br2 - b2, axis=1) < 0.01
    return ok1 * ok2


def robust_match_calibrated(p1, p2, camera1, camera2, matches, config):
    '''Computes robust matches by estimating the Essential matrix via RANSAC.
    '''

    if len(matches) < 8:
        return np.array([])

    p1 = p1[matches[:, 0]][:, :2].copy()
    p2 = p2[matches[:, 1]][:, :2].copy()
    b1 = camera1.pixel_bearings(p1)
    b2 = camera2.pixel_bearings(p2)

    threshold = config['robust_matching_threshold']
    T = pyopengv.relative_pose_ransac(b1, b2, "STEWENIUS", 1 - np.cos(threshold), 1000)

    inliers = compute_inliers_bearings(b1, b2, T)

    return matches[inliers]


def robust_match(p1, p2, camera1, camera2, matches, config):
    if (camera1.projection_type == 'perspective'
            and camera1.k1 == 0.0
            and camera2.projection_type == 'perspective'
            and camera2.k1 == 0.0):
        return robust_match_fundamental(p1, p2, matches, config)
    else:
        return robust_match_calibrated(p1, p2, camera1, camera2, matches, config)


def good_track(track, min_length):
    if len(track) < min_length:
        return False
    images = [f[0] for f in track]
    if len(images) != len(set(images)):
        return False
    return True


def create_tracks_graph(features, colors, matches, tag_features, tag_idx, tag_colors, tag_matches, tag_ids, config):
    
    # feature track setup
    logger.debug('Merging features onto tracks')
    uf = UnionFind()
    for im1, im2 in matches:
        for f1, f2 in matches[im1, im2]:
            uf.union((im1, f1), (im2, f2))
    
    sets = {}
    for i in uf:
        p = uf[i]
        if p in sets:
            sets[p].append(i)
        else:
            sets[p] = [i]
    
    tracks = [t for t in sets.values() if good_track(t, config.get('min_track_length', 2))]
    logger.debug('Good tracks: {}'.format(len(tracks)))
    #print '===== tracks ====='
    #print tracks

    # tag track setup
    if config.get('tag_tracks',False):
        logger.debug('Merging tag features into tracks')
        uf = UnionFind()
        for im1, im2 in tag_matches:
            for f1, f2, tag_id in tag_matches[im1, im2]:
                uf.union((im1,f1,tag_id),(im2,f2,tag_id))

        sets = {}
        for i in uf:
            p = uf[i]
            if p in sets:
                sets[p].append(i)
            else:
                sets[p] = [i]

        tag_tracks = [t for t in sets.values()]
        logger.debug('Good tag feature tracks: {}'.format(len(tag_tracks)))
    #print '===== tag tracks ====='
    #print tag_tracks

    # create feature tracks graph
    print_one_track = 10
    tracks_graph = nx.Graph()
    for track_id, track in enumerate(tracks):
        for image, featureid in track:
            if image not in features:
                continue
            x, y = features[image][featureid]
            #if print_one_track > 0:
            #    print image,':  x = ',str(x), '. y = ',str(y)
            r, g, b = colors[image][featureid]
            tracks_graph.add_node(image, bipartite=0)
            tracks_graph.add_node(str(track_id), bipartite=1)
            tracks_graph.add_edge(image,
                                  str(track_id),
                                  feature=(x, y),
                                  feature_id=featureid,
                                  feature_color=(float(r), float(g), float(b)),
                                  tag_feature=0,
                                  tag_id=0,
                                  corner_id=0)
    #    if print_one_track >= 0:
    #        print_one_track -= 1
    #print '|'

    # add tag tracks to graph
    if config.get('tag_tracks',False):
        
        addt = len(tracks)
        print_one_track = True
        for track_id, track in enumerate(tag_tracks):
            for image, featureid, tagid in track:
                if image not in tag_features:
                    continue
                tag_track_id = addt + track_id
                x, y = tag_features[image][featureid]
                #if print_one_track:
                #    print image,':  x = ',str(x), '. y = ',str(y)
                r, g, b = tag_colors[image][featureid]
                cid = tag_idx[image][featureid]
                if image not in tracks_graph:
                    tracks_graph.add_node(image, bipartite=0)
                tracks_graph.add_node(str(tag_track_id), bipartite=1)
                tracks_graph.add_edge(image,
                                        str(tag_track_id),
                                        feature=(x,y),
                                        feature_id=featureid,
                                        feature_color=(float(r), float(g), float(b)),
                                        tag_feature=1,
                                        tag_id=tagid,
                                        corner_id=cid)
    #    print_one_track = False

    # return
    return tracks_graph


def tracks_and_images(graph):
    """List of tracks and images in the graph."""
    tracks, images = [], []
    for n in graph.nodes(data=True):
        if n[1]['bipartite'] == 0:
            images.append(n[0])
        else:
            tracks.append(n[0])
    return tracks, images


def common_tracks(g, im1, im2):
    """
    Return the list of tracks observed in both images
    :param g: Graph structure (networkx) as returned by :method:`DataSet.tracks_graph`
    :param im1: Image name, with extension (i.e. 123.jpg)
    :param im2: Image name, with extension (i.e. 123.jpg)
    :return: tuple: track, feature from first image, feature from second image
    """
    t1, t2 = g[im1], g[im2]
    tracks, p1, p2 = [], [], []
    for track in t1:
        if track in t2:
            p1.append(t1[track]['feature'])
            p2.append(t2[track]['feature'])
            tracks.append(track)
    p1 = np.array(p1)
    p2 = np.array(p2)
    return tracks, p1, p2


def all_common_tracks(graph, tracks, include_features=True, min_common=50):
    """
    Returns a dictionary mapping image pairs to the list of tracks observed in both images
    :param graph: Graph structure (networkx) as returned by :method:`DataSet.tracks_graph`
    :param tracks: list of track identifiers
    :param include_features: whether to include the features from the images
    :param min_common: the minimum number of tracks the two images need to have in common
    :return: tuple: im1, im2 -> tuple: tracks, features from first image, features from second image
    """
    track_dict = defaultdict(list)
    for tr in tracks:
        track_images = sorted(graph[tr].keys())
        for pair in combinations(track_images, 2):
            track_dict[pair].append(tr)
    common_tracks = {}
    for k, v in track_dict.iteritems():
        if len(v) < min_common:
            continue
        if include_features:
            t1, t2 = graph[k[0]], graph[k[1]]
            p1 = np.array([t1[tr]['feature'] for tr in v])
            p2 = np.array([t2[tr]['feature'] for tr in v])
            ontag = [t2[tr]['tag_feature'] for tr in v]
            tag_id = [t2[tr]['tag_id'] for tr in v]
            corner_id = [t2[tr]['corner_id'] for tr in v]
            common_tracks[k] = (v, p1, p2, ontag, tag_id, corner_id)
        else:
            common_tracks[k] = v
    return common_tracks


def create_tags_graph(tag_matches, config):
    
    # tag track setup
    logger.debug('Merging tags into tracks')
    uf = UnionFind()
    for im1, im2 in tag_matches:
        for f1, f2, tagid in tag_matches[im1, im2]:
            uf.union((im1, tagid), (im2, tagid))
    
    sets = {}
    for i in uf:
        p = uf[i]
        if p in sets:
            sets[p].append(i)
        else:
            sets[p] = [i]
    
    tag_tracks = [t for t in sets.values() if good_track(t, config.get('min_track_length', 2))]
    logger.debug('Good tag tracks: {}'.format(len(tag_tracks)))

    # create feature tracks graph
    tags_graph = nx.Graph()
    for track_id, track in enumerate(tag_tracks):
        for image, tagid in track:
            if image not in tags_graph:
                tags_graph.add_node(image, bipartite=0)
            if tagid not in tags_graph:
                tags_graph.add_node(tagid, bipartite=1)
            tags_graph.add_edge(image, tagid)

    # return
    return tags_graph

def tag_connected_components(input_graph):

    # split graph into connected component subgraphs, sorted largest to smallest
    graphs = list(nx.connected_component_subgraphs(input_graph))

    # for each graph, count number of images
    num_imgs_in_graph = []
    num_tags_in_graph = []
    num_tags_in_images = []
    for graph in graphs:
        
        # count images for graph
        imgcount = 0
        tagcount = 0
        taginimagecount = {}

        # for each node
        for n in graph.nodes(data=True):

            # if node is image
            if n[1]['bipartite'] == 0:
                taginimagecount[n[0]] = len(graph[n[0]])
                imgcount += 1
            else:
                tagcount += 1

        # save number of images
        num_imgs_in_graph.append(imgcount)
        num_tags_in_graph.append(tagcount)
        num_tags_in_images.append(taginimagecount)

    # sort graph by num_ims_in_graph
    sorted_zip = sorted(zip(num_imgs_in_graph,graphs,num_tags_in_graph,num_tags_in_images),reverse=True)
    graphs = [x for _,x,_,_ in sorted_zip]
    num_imgs_in_graph = [x for x,_,_,_ in sorted_zip]
    num_tags_in_graph = [x for _,_,x,_ in sorted_zip]
    num_tags_in_images = [x for _,_,_,x in sorted_zip]

    # store in struct
    subgraph_list = []
    for i,graph in enumerate(graphs):
        tagsubgraph = types.TagSubGraph()
        tagsubgraph.graph = graph
        tagsubgraph.num_imgs = num_imgs_in_graph[i]
        tagsubgraph.num_tags = num_tags_in_graph[i]
        tagsubgraph.num_tags_in_images = num_tags_in_images[i]
        subgraph_list.append(tagsubgraph)

    # return
    return subgraph_list