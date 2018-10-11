# Improved Structure from Motion Using Fiducial Marker Matching


## Introduction ##
This work explores how to use the presence of fiducial markers in scenes to improve structure from motion. It was originally published in ECCV 2018 (see citation below). This is the location of the source that is actively being developed. For access to the datasets used in the paper and more information about the method, experiments, and results, see the companion page for this work [here](http://degol2.web.engr.illinois.edu/pages/TagSfM_ECCV18.html).

You can contact Joseph DeGol (degol2@illinois.edu) with any questions, problems, or suggestions.

## License ##
This code is released under the [BSD 2-Clause "Simplified" License](https://github.com/CogChameleon/MarkerSfM/blob/master/LICENSE). This work is built on top of [OpenSfM](https://github.com/mapillary/OpenSfM) which is also released under the [BSD 2-Clause "Simplified" License](https://github.com/mapillary/OpenSfM/blob/master/LICENSE). There are also several dependencies including [OpenCV](https://opencv.org/), [OpenGV](http://laurentkneip.github.io/opengv/), [Ceres Solver](http://ceres-solver.org/), and [Boost Python](https://www.boost.org/) (among others), each released with a license that may be worth checking depending on your needs.


## Citing ##
If you find this work useful, please consider citing:
```
@inproceedings{DeGol:ECCV:18,
  author    = {Joseph DeGol and Timothy Bretl and Derek Hoiem},
  title     = {Improved Structure from Motion Using Fiducial Marker Matching},
  booktitle = {ECCV},
  year      = {2018}
}
```


## Source ## 
Follow the steps below to install and build this repo. These steps were tested for Ubuntu 14.04, 16.04, and 18.04. Basically all of the dependencies match those of [OpenSfM](https://github.com/mapillary/OpenSfM). Note also that OpenSfM supports Docker, which could be used as a starting point for these instructions.

### Dependencies ###
The easiest way to install the dependencies is to use the `install_dependencies.sh` script in the `scripts` directory. This script has been tested with Ubuntu 14.04, Ubuntu 16.04 and Ubuntu 18.04. For other operating systems, I suggest using the script as a guide for what dependencies are required. To run this install script, use the following commands:
```
sudo apt-get install git
git clone https://github.com/CogChameleon/MarkerSfM.git
cd MarkerSfM
bash scripts/install_dependencies.sh 2>&1 | tee install_dependencies.log
```
This will write the installation output to the install_dependencies.log in case there are any problems. 

### Marker SfM ###
After that, from the `MarkerSfM` directory, use the following command to build MarkerSfM.
```
python setup.py build
```


## Usage ##
A run script is provided to process the ece_floor4_wall images. This script is located in the `scripts` directory, and it is called `run_markersfm.sh`. Note, you should provide the ABSOLUTE PATH to the dataset you want to process. To run the script with the demo data, type:
```
cd scripts
bash run_markersfm.sh /ABSOLUTE/PATH/TO/MarkerSfM/data/ece_floor4_wall
```

There are also a bunch of parameters that can be set in the config.yaml file. I suggest that you copy the config.yaml in the project to each data folder you want to process. The main parameter that you definitely want to change is `processes`, which you should set to the number of vcpu's on your machine.


## Data ##
Some demo data is provided with the repository in the `data` directory to ensure things are running correctly. All the data from the paper can be downloaded from [here](http://degol2.web.engr.illinois.edu/pages/TagSfM_ECCV18.html).
