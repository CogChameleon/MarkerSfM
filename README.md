# Improved Structure from Motion Using Fiducial Marker Matching


## Introduction ##
This work explores how to use the presence of fiducial markers in scenes to improve structure from motion. It was originally published in ECCV 2018 (see citation below). This is the location of the source that is actively being developed. For access to the datasets used in the paper and more information about the method, experiments, and results, see the companion page for this work [here](http://degol2.web.engr.illinois.edu/pages/TagSfM_ECCV18.html).

You can contact Joseph DeGol (degol2@illinois.edu) with any questions, problems, or suggestions.

## License ##
This code is released under the MIT License (see the LICENSE file for details). This work is built on top of [OpenSfM](https://github.com/mapillary/OpenSfM) which is released under the [BSD 2-Clause "Simplified" License](https://github.com/mapillary/OpenSfM/blob/master/LICENSE). There are also several dependencies including [OpenCV](https://opencv.org/), [OpenGV](http://laurentkneip.github.io/opengv/), [Ceres Solver](http://ceres-solver.org/), and [Boost Python](https://www.boost.org/), each released with a license that may be worth checking depending on your needs.


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
Follow the steps below to install and build this repo. These steps should work for Ubuntu 14.04, 16.04, and 18.04. Any differences between the ubuntu distributions are noted below. These steps are adapted from those listed for [OpenSfM](https://github.com/mapillary/OpenSfM). Note also, that OpenSfM supports Docker, which could be used as a starting point for these instructions.

#### Common ####
These are common Unix libraries used to build c++ programs from source.
```
sudo apt-get update
sudo apt-get install git
sudo apt-get install build-essential
sudo apt-get install cmake
sudo apt-get install pkg-config
```

#### OpenCV ####
OpenCV is required to build and run ChromaTag. These instructions are adapted from the [this OpenCV tutorial](http://docs.opencv.org/3.1.0/d7/d9f/tutorial_linux_install.html).

First, download OpenCV 3.1.0 or higher: https://github.com/Itseez/opencv/archive/3.1.0.zip.

Next, Install these packages:
```
sudo apt-get install libgtk2.0-dev 
sudo apt-get install libavcodec-dev 
sudo apt-get install libavformat-dev 
sudo apt-get install libswscale-dev
sudo apt-get install python-dev python-numpy 
sudo apt-get install libtbb2 libtbb-dev 
sudo apt-get install libjpeg-dev 
sudo apt-get install libpng-dev 
sudo apt-get install libtiff-dev 
sudo apt-get install libjasper-dev 
sudo apt-get install libdc1394-22-dev
```

Finally, build OpenCV
```
unzip opencv-3.1.0.zip
cd opencv-3.1.0
mkdir build
cd build
cmake -D CMAKE_BUILD_TYPE=Release -D CMAKE_INSTALL_PREFIX=/usr/local ..
make -j4
sudo make install
```

OpenCV should now be installed in your system. If you choose to download a different version from 3.1.0, change the text above appropriately. If these instructions do not work for your version of OpenCV, please check the OpenCV provided tutorial for your version because there may be small differences.

#### OpenGV ####

#### Ceres ####

### MarkerSfM ###
To clone and build ChromaTag, move to a directory where you want the ChromaTag source to live and then run the following commands in a Unix terminal.
```
git clone <insert git path>
cd MarkerSfM
python setup.py build
```

The built executables will be in `.../<pathtobin>` and the libraries will be in `.../<pathtolibs>`.
```
cd <bins>
ls
```


## Usage ##
A run script is provided to process the toy images. This script uses the `<insert_script>` program in `.../<insert_path>`. To run the script, type:
```
cd <script_path>
bash <insert_script>
```


## Data ##
Some toy data is provided with the repository to ensure things are running correctly.
