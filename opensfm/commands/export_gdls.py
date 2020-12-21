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
    name = 'export_gdls'
    help = 'exports a reconstruction into four files representing four reconstructions that can aligned using gDLS'

    def add_arguments(self, parser):
        parser.add_argument('dataset', help='dataset with completed reconstruction to process')

    def run(self, args):

        # recon
        data = dataset.DataSet(args.dataset)
        images = data.images()
        cam = data.load_camera_models()
        graph = data.load_tracks_graph()
        reconstructions = data.load_reconstruction()

        self.write_alignment_problem(images[:len(images)//2], images[len(images)//2:], reconstructions[0], graph, os.path.join(data.data_path,'half1half2.txt'))
        self.write_alignment_problem(images[len(images)//2:], images[:len(images)//2], reconstructions[0], graph, os.path.join(data.data_path,'half2half1.txt'))
        self.write_alignment_problem(images[0::2],images[1::2], reconstructions[0], graph, os.path.join(data.data_path,'weave1weave2.txt'))
        self.write_alignment_problem(images[1::2],images[0::2], reconstructions[0], graph, os.path.join(data.data_path,'weave2weave1.txt'))

    def write_alignment_problem(self, setA, setB, rec, graph, outpath):

        # variables
        points = rec.points
        shots = rec.shots
        lines = []
        
        # for each point
        for point_id, point in points.iteritems():

            # x,y,z
            coordA = point.coordinates
        
            # view list
            view_list = graph[point_id]

            # for each observation of that point
            for shot_key, view in view_list.iteritems():
                
                # if it was localized and it is in setB
                if shot_key in shots.keys() and shot_key in setB:

                    # get origin and bearing 
                    shotB = shots[shot_key]
                    o = shotB.pose.get_origin()
                    b = coordA - o
                    n = np.linalg.norm(b)
                    if n != 0:
                        b = b / n

                    # store as line
                    line = "{} {} {} {} {} {} {} {} {}\n".format(coordA[0], coordA[1], coordA[2], o[0], o[1], o[2], b[0], b[1], b[2])
                    lines.append(line)

        with open(outpath,'w') as fid:
            fid.writelines(lines)