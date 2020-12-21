import logging
import time
import glob
import os
import yaml

from opensfm import dataset
from opensfm import reconstruction

logger = logging.getLogger(__name__)


class Command:
    name = 'reconstruct'
    help = "Compute the reconstruction"

    def add_arguments(self, parser):
        parser.add_argument('dataset', help='dataset to process')
        parser.add_argument('--experiments', help='tree of folders with config.yaml files for generating experiments')

    def override_config(self,data,filepath):
        
        # if file exists
        if os.path.isfile(filepath):

            # open file
            with open(filepath) as fin:
                new_config = yaml.load(fin)
            
            # if file opened
            if new_config:

                # read values in config
                for k, v in new_config.items():
                    if data.config[k] != v:
                        print('found override: [',k,'] = ', str(v))
                        data.config[k] = v

    def run(self, args):
        start = time.time()
        data = dataset.DataSet(args.dataset)

        # experiments directory tree given
        if args.experiments:
            
            # check that directory exists
            if not os.path.isdir(args.experiments):
                print('--experiments option given but directory does not exist.')
                return

            # find yaml files in experiments directory
            yamls = glob.glob( os.path.join(args.experiments,'*.yaml'))
            if not yamls:
                print('No yaml files found in ', args.experiments)
                return
            for yaml in yamls:

                # setup
                data = dataset.DataSet(args.dataset)
                config_path = os.path.join(args.experiments,yaml)
                self.override_config(data,config_path)
                data.config['experiments_path'] = args.experiments
                start = time.time()

                # run recon
                if data.config.get('tag_tracks',False) or data.config.get('resection_with_tags',False):
                    reconstruction.incremental_reconstruction_with_tags(data)
                else:
                    reconstruction.incremental_reconstruction(data)

                # shutdown
                end = time.time()
                reconstruction_name = data.reconstruction_name_from_settings()
                log_path = os.path.join(args.experiments,reconstruction_name+'.log')
                with open(log_path,'w') as fout:
                    fout.write('reconstruct: {0}\n'.format(end-start))

        # normal run
        else:
            # reconstruction type
            if data.config.get('tag_tracks',False) or data.config.get('resection_with_tags',False):
                reconstruction.incremental_reconstruction_with_tags(data)
            else:
                reconstruction.incremental_reconstruction(data)
        
            # profile
            end = time.time()
            with open(data.profile_log(), 'a') as fout:
                fout.write('reconstruct: {0}\n'.format(end - start))
