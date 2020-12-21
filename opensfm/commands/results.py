import logging
import time
import networkx as nx
from networkx.algorithms import bipartite
import numpy as np
try:
    import matplotlib.pyplot as plt
except:
    pass
from opensfm import dataset
from opensfm import matching

logger = logging.getLogger(__name__)


class Command:
    name = 'results'
    help = "returns the results for a 3D reconstruction"

    def add_arguments(self, parser):
        parser.add_argument('dataset', help='dataset to process')
        parser.add_argument('-g','--show_tag_graph', help='display tag matching graph', default=False)

    def read_runtime_from_profile(self, data):

        # time
        time = 0

        # open file
        with open(data.profile_log(), 'r') as fin:
            for line in fin:
                tokens = line.split(':')
                time += float( tokens[1] )

        # return
        return time

    def draw_tag_graph(self,tags_graph):

        X, Y = bipartite.sets(tags_graph)
        pos = dict()
        pos.update( (n, (3*i, 1)) for i, n in enumerate(X) ) # put nodes from X at x=1
        pos.update( (n, (3*i, 2)) for i, n in enumerate(Y) ) # put nodes from Y at x=2
        nx.draw(tags_graph, pos=pos, with_labels = True, node_size = 600, node_shape = 's',font_size='10')
        plt.show()

    def run(self, args):
        data = dataset.DataSet(args.dataset)
        images = data.images()

        # Read local features
        logging.info('reading features')
        features = {}
        colors = {}
        for im in images:
            p, f, c = data.load_features(im)
            features[im] = p[:, :2]
            colors[im] = c

        # Read tag features
        tag_features = {}
        tag_colors = {}
        tag_idx = {}
        tag_ids = {}
        for im in images:
            try:
                p, f, i, c = data.load_tag_features(im)
                tag_features[im] = p
                tag_colors[im] = c
                tag_idx[im] = i
                tag_ids[im] = f
            except IOError:
                continue

        # start report
        print('=============== ' + args.dataset + '===============')

        # Matching Results:

        # Draw Tag Graph
        if args.show_tag_graph:
            try:
                tags_graph = data.load_tags_graph()
                self.draw_tag_graph(tags_graph)
            except:
                pass

        # Reconstruction Results
        try:
            reconstructions = data.load_reconstruction()
        except:
            return

        if reconstructions:

            # Number of Reconstructions
            print('    Number of Reconstructions: ' + str(len(reconstructions)))

            # Number of Images Localized in First Reconstruction
            recon0 = reconstructions[0]
            shots0 = recon0.shots
            print('    Localized Ims in Largest:  ' + str(len(shots0)))

            # Reprojection Error
            points0 = recon0.points
            nor_reproj_error_list = []
            tag_reproj_error_list = []
            tot_reproj_error_list = []
            for point in points0.values():
                if point.reprojection_error:
                    if point.on_tag:
                        tag_reproj_error_list.append(point.reprojection_error)
                    else:
                        nor_reproj_error_list.append(point.reprojection_error)
                    tot_reproj_error_list.append(point.reprojection_error)
            if len(nor_reproj_error_list) > 0:
                print('    Avg Reproj Error:          ' + '{0:.6f}'.format(np.mean(nor_reproj_error_list)) + ' (' + str(len(nor_reproj_error_list)) + ' points)')
                print('    Median Reproj Error:       ' + '{0:.6f}'.format(np.median(nor_reproj_error_list)))
            if len(tag_reproj_error_list) > 0:
                print('    Avg Tag Reproj Error:      ' + '{0:.6f}'.format(np.mean(tag_reproj_error_list)) + ' (' + str(len(tag_reproj_error_list)) + ' points)')
                print('    Median Tag Reproj Error:   ' + '{0:.6f}'.format(np.median(tag_reproj_error_list)))
            if len(tot_reproj_error_list) > 0:
                print('    Avg Total Reproj Error:    ' + '{0:.6f}'.format(np.mean(tot_reproj_error_list)) + ' (' + str(len(tot_reproj_error_list)) + ' points)')
                print('    Median Total Reproj Error: ' + '{0:.6f}'.format(np.median(tot_reproj_error_list)))
                print('    Avg Total Reproj Error:    ' + '{0:.6f}'.format(4032.0*np.mean(tot_reproj_error_list)) + ' (' + str(len(tot_reproj_error_list)) + ' points)')
                print('    Median Total Reproj Error: ' + '{0:.6f}'.format(4032.0*np.median(tot_reproj_error_list)))

            # Time to process
            print('    Time to Process Dataset:   ' + '{0:.2f}'.format( self.read_runtime_from_profile(data) ) + ' seconds')

        else:
            print('    Number of Reconstructions: ' + str(len(reconstructions)))
        print('')
