import logging
from multiprocessing import Pool
import time
import os
import sys

import numpy as np
import cv2
from opensfm import dataset
from opensfm import features

logger = logging.getLogger(__name__)


class Command:
    name = 'detect_features'
    help = 'Compute features for all images'

    def add_arguments(self, parser):
        parser.add_argument('dataset', help='dataset to process')

    def run(self, args):
        data = dataset.DataSet(args.dataset)
        images = data.images()
        try:
            tags = data.load_tag_detection()
        except:
            tags = {image: [] for image in images}
        if not tags:
            tags = {image: [] for image in images}
        arguments = [(image, tags[image], data) for image in images]

        start = time.time()
        processes = data.config.get('processes', 1)
        if processes == 1:
            for arg in arguments:
                detect(arg)
        else:
            p = Pool(processes)
            p.map(detect, arguments)
        end = time.time()
        with open(data.profile_log(), 'a') as fout:
            fout.write('detect_features: {0}\n'.format(end - start))


def detect(args):
    image, tags, data = args
    logger.info('Extracting {} features for image {}'.format(data.feature_type().upper(), image))
    DEBUG = 0
    
    # check if features already exist
    if not data.feature_index_exists(image):
        
        mask = data.mask_as_array(image)
        if mask is not None:
            logger.info('Found mask to apply for image {}'.format(image))
        preemptive_max = data.config.get('preemptive_max', 200)
        p_unsorted, f_unsorted, c_unsorted = features.extract_features(data.image_as_array(image), data.config, mask)
        if len(p_unsorted) == 0:
            return

        #===== prune features in tags =====#
        if data.config.get('prune_features_on_tags',False):

            # setup
            img = cv2.imread( os.path.join(data.data_path,'images',image) )
            [height, width, _] = img.shape
            p_denorm = features.denormalized_image_coordinates(p_unsorted, width, height)

            # expand tag contour with grid points beyond unit square
            expn = 2.0
            gridpts = np.array([[-expn,expn],[expn,expn],[expn,-expn],[-expn,-expn]], dtype='float32')

            # find features to prune
            rm_list = []
            for tag in tags:
                
                # contour from tag region
                contours = np.array(tag.corners)
                if DEBUG > 0:
                    for i in range(0,3):
                        cv2.line(img,(tag.corners[i,0].astype('int'), tag.corners[i,1].astype('int')),(tag.corners[i+1,0].astype('int'), tag.corners[i+1,1].astype('int')),[0,255,0],12)
                    cv2.line(img,(tag.corners[3,0].astype('int'), tag.corners[3,1].astype('int')),(tag.corners[0,0].astype('int'), tag.corners[0,1].astype('int')),[0,255,0],12)
                
                # scale contour outward
                H = np.array(tag.homography, dtype='float32')
                contours_expanded = cv2.perspectiveTransform(np.array([gridpts]),H)
                
                # for each point
                for pidx in range(0,len(p_unsorted)):
                    
                    # point
                    pt = p_denorm[pidx,0:2]

                    # point in contour
                    inout = cv2.pointPolygonTest(contours_expanded.astype('int'), (pt[0], pt[1]), False)

                    # check result   
                    if inout >= 0:
                        rm_list.append(pidx)

            # prune features
            p_unsorted = np.delete(p_unsorted, np.array(rm_list), axis = 0)
            f_unsorted = np.delete(f_unsorted, np.array(rm_list), axis = 0)
            c_unsorted = np.delete(c_unsorted, np.array(rm_list), axis = 0)
            
            # debug
            if DEBUG > 0:
                p_denorm = np.delete(p_denorm, np.array(rm_list), axis = 0)
                for pidx in range(0,len(p_denorm)):
                    pt = p_denorm[pidx,0:2]
                    cv2.circle(img,(pt[0].astype('int'),pt[1].astype('int')),5,[0,0,255],-1)

                cv2.namedWindow('ShowImage',cv2.WINDOW_NORMAL)
                height, width, channels = img.shape
                showw = max(752,width / 4)
                showh = max(480,height / 4)
                cv2.resizeWindow('ShowImage',showw,showh)
                cv2.imshow('ShowImage',img)
                cv2.waitKey(0)
        #===== prune features in tags =====#

        # sort for preemptive
        size = p_unsorted[:, 2]
        order = np.argsort(size)
        p_sorted = p_unsorted[order, :]
        f_sorted = f_unsorted[order, :]
        c_sorted = c_unsorted[order, :]
        p_pre = p_sorted[-preemptive_max:]
        f_pre = f_sorted[-preemptive_max:]

        # save
        data.save_features(image, p_sorted, f_sorted, c_sorted)
        data.save_preemptive_features(image, p_pre, f_pre)

        if data.config.get('matcher_type', 'FLANN') == 'FLANN':
            index = features.build_flann_index(f_sorted, data.config)
            data.save_feature_index(image, index)


    #===== tag features =====#
    if data.config.get('use_apriltags',False) or data.config.get('use_arucotags',False) or data.config.get('use_chromatags',False):

        # setup
        try:
            tags_all = data.load_tag_detection()
        except:
            return
        tags = tags_all[image]
        pt = []
        ft = []
        ct = []
        it = []
        imexif = data.load_exif(image)

        # for each tag in image
        for tag in tags:

            # normalize corners
            img = cv2.imread( os.path.join(data.data_path,'images',image) )
            [height, width, _] = img.shape
            #print 'width = ',str(imexif['width'])
            #print 'height= ',str(imexif['height'])
            #print 'width2= ',str(width)
            #print 'heigh2= ',str(height)
            norm_tag_corners = features.normalized_image_coordinates(tag.corners, width, height)#imexif['width'], imexif['height'])

            # for each corner of tag
            for r in range(0,4):

                # tag corners
                pt.append( norm_tag_corners[r,:] )

                # tag id
                ft.append( tag.id )
                
                # colors
                ct.append( tag.colors[r,:] )
                
                # corner id (0,1,2,3)
                it.append( r )
        
        # if tag features found
        if pt:
            pt = np.array(pt)
            ft = np.array(ft)
            ct = np.array(ct)
            it = np.array(it)
            data.save_tag_features(image, pt, ft, it, ct)
        #===== tag features =====#
