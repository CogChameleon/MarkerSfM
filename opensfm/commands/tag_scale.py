import logging
import time
import glob
import os
import yaml

from opensfm import dataset
from opensfm import reconstruction
from opensfm import align

logger = logging.getLogger(__name__)


class Command:
    name = 'tag_scale'
    help = "Compute the scale to scale a reconstruction based on tag size"

    def add_arguments(self, parser):
        parser.add_argument('dataset', help='dataset to process')

    def run(self, args):
        start = time.time()
        data = dataset.DataSet(args.dataset)
        config = data.config
        tag_scale_method = config.get('tag_scale_method','L2')

        # Load Reconstructions
        try:
            reconstructions = data.load_reconstruction()
        except:
            return

        # successful load
        if reconstructions:

            # Just take the biggest and first reconstruction
            recon = reconstructions[0]

            # get median (L1) and mean (L2) scales
            config['tag_scale_method'] = 'L1'
            sL1, AL1, bL1, sigma1 = align.scale_reconstruction_tags(recon, config)
            config['tag_scale_method'] = 'L2'
            sL2, AL2, bL2, sigma2 = align.scale_reconstruction_tags(recon, config)

            # write to file
            with open(os.path.join(data.data_path,'priors_scale.txt'),'w') as sout:
                sout.write('{0} {1} {2} {3}'.format(sL1, sL2, sigma1, sigma2))

            if tag_scale_method == 'L1':
                align.apply_similarity(recon, sL1, AL1, bL1)
            elif tag_scale_method == 'L2':
                align.apply_similarity(recon, sL2, AL2, bL2)

            # save scaled as scaled
            reconstructions[0] = recon
            data.save_reconstruction(reconstructions, os.path.join(data.data_path,'reconstruction_scaled.json'))
            
        # profile
        end = time.time()
        with open(data.profile_log(), 'a') as fout:
            fout.write('tag_scale: {0}\n'.format(end - start))
