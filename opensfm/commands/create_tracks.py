import logging
import time

from opensfm import dataset
from opensfm import matching

logger = logging.getLogger(__name__)


class Command:
    name = 'create_tracks'
    help = "Link matches pair-wise matches into tracks"

    def add_arguments(self, parser):
        parser.add_argument('dataset', help='dataset to process')

    def run(self, args):
        start = time.time()
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

        # Read matches
        matches = {}
        for im1 in images:
            try:
                im1_matches = data.load_matches(im1)
            except IOError:
                continue
            for im2 in im1_matches:
                matches[im1, im2] = im1_matches[im2]

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

        # Read tag pt matches
        tag_matches = {}
        for im1 in images:
            try:
                im1_tag_matches = data.load_tag_matches(im1)
            except IOError:
                continue
            for im2 in im1_tag_matches:
                tag_matches[im1, im2] = im1_tag_matches[im2]

        # create tracks graph
        tracks_graph = matching.create_tracks_graph(features, colors, matches, tag_features, tag_idx, tag_colors, tag_matches, tag_ids, data.config)
        data.save_tracks_graph(tracks_graph)

        end = time.time()
        with open(data.profile_log(), 'a') as fout:
            fout.write('create_tracks: {0}\n'.format(end - start))
