import logging
import time
import sys
import os
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
    name = 'export_simtrancorr'
    help = 'exports the data of two reconstructions s.t. a similarity transformation can be computed to align them using e.g. gDLS'

    def add_arguments(self, parser):
        parser.add_argument('dataset1', help='dataset1 with completed reconstruction to process')
        parser.add_argument('dataset2', help='dataset2 with completed reconstruction to process')

    def run(self, args):

        # recon 1
        data1 = dataset.DataSet(args.dataset1)
        images1 = data1.images()
        cam1 = data1.load_camera_models()
        graph1 = data1.load_tracks_graph()
        reconstructions1 = data1.load_reconstruction()

        # features 1
        features1 = {}
        colors1 = {}
        for im in images1:
            p, f, c = data1.load_features(im)
            features1[im] = p[:, :2]
            colors1[im] = c
        
        #recon 2
        data2 = dataset.DataSet(args.dataset2)
        images2 = data2.images()
        cam2 = data2.load_camera_models()
        graph2 = data2.load_tracks_graph()
        reconstructions2 = data2.load_reconstruction()

        # features 2
        features2 = {}
        colors2 = {}
        for im in images2:
            p, f, c = data2.load_features(im)
            features2[im] = p[:, :2]
            colors2[im] = c

        # matches1to2 to graph
        matches12 = {}
        for im1 in images1:
            try:
                im1_matches = data1.load_other_recon_matches(im1)
            except IOError:
                continue
            for im2 in im1_matches:
                matches12[im1, im2] = im1_matches[im2]
        graph12 = [] #matching.create_tracks_graph(features1, colors1, matches12, {}, {}, {}, {}, {}, data1.config)

        # matches2to1 to graph
        matches21 = {}
        for im1 in images2:
            try:
                im1_matches = data2.load_other_recon_matches(im1)
            except IOError:
                continue
            for im2 in im1_matches:
                matches21[im1, im2] = im1_matches[im2]
        graph21 = [] #matching.create_tracks_graph(features2, colors2, matches21, {}, {}, {}, {}, {}, data2.config)

        #write both ways
        self.write_corrsAtoB(reconstructions1[0], graph1, matches12, reconstructions2[0], features2, os.path.join(data1.data_path,'simt_problem.txt'))
        self.write_corrsAtoB(reconstructions2[0], graph2, matches21, reconstructions1[0], features1, os.path.join(data2.data_path,'simt_problem.txt'))

    # camera center, rotation col0, rotation col1, rotation_col2, img width, img_height, focal length, pixel ray direction, 3D point
    def write_corrsAtoB(self, recA, graphA, matchesAB, recB, featB, outpath):

        # points
        pointsA = recA.points
        shotsA = recA.shots
        shotsB = recB.shots
        lines = []

        # for each point
        for pointA_id, pointA in pointsA.iteritems():

            # x,y,z in A frame
            coordA = pointA.coordinates
        
            # view list
            view_listA = graphA[pointA_id]

            # for each observation of that point
            for shot_keyA, viewA in view_listA.iteritems():
                if shot_keyA in shotsA.keys():

                    # get feature id in frame A for a given view
                    fidA = viewA['feature_id']
                    shotA = shotsA[shot_keyA]
                    camA = shotA.camera
                    poseA = shotA.pose
                    
                    # for each image in recon B
                    for shot_keyB in shotsB.keys():

                        # shot in B frame
                        shotB = shotsB[shot_keyB]

                        # matches between shotA and shotB
                        matchesAB_shotsAB = matchesAB[shot_keyA, shot_keyB]
                        if np.array(matchesAB_shotsAB).size != 0:
                            
                            #find matches where A is fidA
                            matchesAB_shotsAB_fidAs = np.where(matchesAB_shotsAB[...,0] == fidA)
                            
                            # for each match in shotB where the shotA feature index is fidA, find the origin and bearing
                            for matchesAB_shotsAB_fidA in matchesAB_shotsAB_fidAs:
                                if matchesAB_shotsAB_fidA.size != 0:
                                    o = shotB.pose.get_origin()
                                    pAB = poseA.compose(shotB.pose)
                                    R = pAB.get_rotation_matrix()
                                    t = pAB.translation
                                    b = coordA - o
                                    n = np.linalg.norm(b)
                                    if n != 0:
                                        b = b / n
                                    line = "{} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {}\n".format(
                                        o[0], o[1], o[2],                   # camera center             (1-3)
                                        R[0,0], R[1,0], R[2,0],             # rotation matrix col 1     (4-6)
                                        R[0,1], R[1,1], R[2,1],             # rotation matrix col 2     (7-9)
                                        R[0,2], R[1,2], R[2,2],             # rotation matrix col 3     (10-12)
                                        t[0], t[1], t[2],                   # tx, ty, tz                (13-15)
                                        camA.width, camA.height,            # image width and height    (16,17)
                                        camA.focal,                         # focal length              (18)
                                        b[0], b[1], b[2],                   # bearing vector            (19-21)
                                        coordA[0], coordA[1], coordA[2]     # 3D point                  (22-24)
                                        )
                                    #line = "{} {} {} {} {} {} {} {} {}\n".format(coordA[0], coordA[1], coordA[2], o[0], o[1], o[2], b[0], b[1], b[2])
                                    lines.append(line)
                                    #print(featB[shot_keyB][matchesAB_shotsAB_fidA[0]])
                        
        with open(outpath,'w') as fid:
            fid.writelines(lines)               