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
    name = 'detect_tags'
    help = 'Detect tags for all images'

    def add_arguments(self, parser):
        parser.add_argument('dataset', help='dataset to process')

    def run(self, args):

        # setup
        data = dataset.DataSet(args.dataset)
        images = data.images()
        try:
            tags = data.load_tag_detection()
            return
        except:
            pass
        start = time.time()

        # make directory
        tag_detections_dir = os.path.join(data.data_path,'tag_detections')
        if not os.path.exists(tag_detections_dir):
            os.makedirs(tag_detections_dir)
        
        # arguments for multiprocessing
        arguments = [(image, data.data_path) for image in images]

        # get num processes
        processes = data.config.get('processes', 1)
        
        # AprilTags
        if data.config.get('use_apriltags', False):

            if processes == 1:
                for arg in arguments:
                    apriltag_detect(arg)
            else:
                p = Pool(processes)
                p.map(apriltag_detect,arguments)

        if data.config.get('use_arucotags', False):
            print 'Use ArucoTags = True but not implemented yet.'
        
        if data.config.get('use_chromatags', False):
            print 'Use ChromaTags = True but not implemented yet.'

        # merge all tag detections into one json
        logger.info('Merging tag detection files into one json.')
        images_with_tag_detections = {}
        for image in images:
            try:
                tag_det = data.load_tag_detection(os.path.join('tag_detections',image+'.json'))
                images_with_tag_detections[image] = tag_det[image]
            except:
                pass
        data.save_tag_detection(images_with_tag_detections)

        # shutdown
        end = time.time()
        with open(data.profile_log(), 'a') as fout:
            fout.write('detect_tags: {0}\n'.format(end - start))

def apriltag_detect(args):

    # split args
    image, data_path = args

    # set paths
    imagepath = os.path.join(data_path,'images',image)
    tag_detections_dir = os.path.join(data_path,'tag_detections')
    jsonpath = os.path.join(tag_detections_dir,image+'.json')
    
    # check if detection exists
    if os.path.isfile(jsonpath):
        return

    # set apriltag tag algorithm
    command = './/detect_apriltag -i ' + imagepath
    #command += ' -r 960'
    command += ' -t 1'
    command += ' -J ' + jsonpath
    
    # run process
    pProc = subprocess.Popen(command, shell=True, cwd=os.path.dirname(os.path.realpath(__file__)) )
    pProc.wait()