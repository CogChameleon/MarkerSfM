import logging
from multiprocessing import Pool
import time
import subprocess
from subprocess import STDOUT
import numpy as np
import os

from opensfm import dataset
from opensfm import features

logger = logging.getLogger(__name__)


class Command:
    name = 'prune_features'
    help = 'Remove all features inside masked regions'

    def add_arguments(self, parser):
        parser.add_argument('dataset', help='dataset to process')

    def run(self, args):

        # setup
        data = dataset.DataSet(args.dataset)
        images = data.images()
        tags = data.load_tag_detection()
        print tags
        #start = time.time()
        
        # get num processes
        #processes = data.config.get('processes', 1)
        
        # choose tag algorithm
        #imagepath = os.path.join(data.data_path,'images')
        #jsonpath = os.path.join(data.data_path,'tag_detections.json')
        #run_command = ['.//detect_apriltag -F ' + imagepath + ' -r 960 -J ' + jsonpath]
        
        # run process
        #pProc = subprocess.Popen(run_command, shell=True, cwd=os.path.dirname(os.path.realpath(__file__)) )
        #pProc.wait()

        # shutdown
        #end = time.time()
        #with open(data.profile_log(), 'a') as fout:
        #    fout.write('detect_features: {0}\n'.format(end - start))
