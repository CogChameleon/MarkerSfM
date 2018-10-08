# Improved Structure from Motion Using Fiducial Marker Matching


## Introduction ##
This work explores how to use the presence of fiducial markers in scenes to improve structure from motion. It was originally published in ECCV 2018 (see citation below). This is the location of the source that is actively being developed. For access to the datasets used in the paper and more information about the method, experiments, and results, see the companion page for this work [here](http://degol2.web.engr.illinois.edu/pages/TagSfM_ECCV18.html).

You can contact Joseph DeGol (degol2@illinois.edu) with any questions, problems, or suggestions.

## License ##
This code is released under the [BSD 2-Clause "Simplified" License](https://github.com/CogChameleon/MarkerSfM/blob/master/LICENSE). This work is built on top of [OpenSfM](https://github.com/mapillary/OpenSfM) which is also released under the [BSD 2-Clause "Simplified" License](https://github.com/mapillary/OpenSfM/blob/master/LICENSE). There are also several dependencies including [OpenCV](https://opencv.org/), [OpenGV](http://laurentkneip.github.io/opengv/), [Ceres Solver](http://ceres-solver.org/), and [Boost Python](https://www.boost.org/), each released with a license that may be worth checking depending on your needs.


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
sudo apt-get install git build-essential cmake pkg-config wget unzip
sudo apt-get install libatlas-base-dev
sudo apt-get install libboost-all-dev
sudo apt-get install libboost-python-dev
sudo apt-get install libsuitesparse-dev
sudo apt-get install libeigen3-dev
sudo apt-get install libgoogle-glog-dev
sudo apt-get install python-dev 
sudo apt-get install python-numpy 
sudo apt-get install python-pip
sudo apt-get install python-pyexiv2
sudo apt-get install python-pyproj
sudo apt-get install python-scipy
sudo apt-get install python-yaml
sudo pip install exifread==2.1.2
sudo pip install gpxpy==1.1.2
sudo pip install networkx==1.11
sudo pip install pyproj==1.9.5.1
sudo pip install pytest==3.0.7
sudo pip install python-dateutil==2.6.0
sudo pip install PyYAML==3.12
sudo pip install xmltodict==0.10.2
```

Next, check what version of cmake you are running by typing
```
cmake --version
```

If the version is less than 3.1.0, follow the instruction below to install an updated version of cmake.
```
sudo apt-get purge cmake
cd ~/Downloads
wget https://cmake.org/files/v3.5/cmake-3.5.2.tar.gz
tar xzvf cmake-3.5.2.tar.gz
cd cmake-3.5.2/
./bootstrap
make -j
sudo make install
```

Now, the version of cmake should show 3.5.2.
```
cmake --version
```
If this command returns `No such file or directory`, you must have `/usr/local/bin` to your path:
```
export PATH=$PATH:/usr/local/bin
```


#### OpenCV ####
OpenCV is required to build and run this code. These instructions are adapted from the [this OpenCV tutorial](http://docs.opencv.org/3.1.0/d7/d9f/tutorial_linux_install.html).

First, download OpenCV 3.4.3.
```
cd ~/Downloads
wget https://github.com/opencv/opencv/archive/3.4.3.zip
```

Next, Install these packages:
```
sudo apt-get install libgtk2.0-dev 
sudo apt-get install libavcodec-dev 
sudo apt-get install libavformat-dev 
sudo apt-get install libswscale-dev
sudo apt-get install libtbb2 libtbb-dev 
sudo apt-get install libjpeg-dev 
sudo apt-get install libpng-dev 
sudo apt-get install libtiff-dev 
sudo apt-get install libjasper-dev 
sudo apt-get install libdc1394-22-dev
```

Finally, build OpenCV
```
unzip 3.4.3.zip
cd opencv-3.4.3
mkdir build
cd build
cmake -D CMAKE_BUILD_TYPE=Release -D CMAKE_INSTALL_PREFIX=/usr/local ..
make -j
sudo make install
```

OpenCV should now be installed in your system. If you choose to download a different version from 3.4.3, change the text above appropriately. If these instructions do not work for your version of OpenCV, please check the OpenCV provided tutorial for your version because there may be small differences. Note that you can also install opencv using apt with `sudo apt-get install libopencv-dev python-opencv`, but I always build from source, so I don't know if this will provide you with the correct version.

#### Ceres ####
Next, we need to build Ceres solver from source and install it.
```
cd ~/Downloads
wget http://ceres-solver.org/ceres-solver-1.10.0.tar.gz
tar xvzf ceres-solver-1.10.0.tar.gz
cd ceres-solver-1.10.0
mkdir build
cd build
cmake .. -DCMAKE_C_FLAGS=-fPIC -DCMAKE_CXX_FLAGS=-fPIC -DBUILD_EXAMPLES=OFF -DBUILD_TESTING=OFF
make -j
sudo make install
```

#### OpenGV ####
Lastly, we need to build OpenGV.
```
cd ~/Downloads
git clone https://github.com/paulinus/opengv.git
cd opengv
mkdir build
cd build
cmake .. -DBUILD_TESTS=OFF -DBUILD_PYTHON=ON
make -j
sudo make install
```

### MarkerSfM ###
To clone and build MarkerSfM, move to a directory where you want the source to live and then run the following commands in a Unix terminal.
```
git clone https://github.com/CogChameleon/MarkerSfM.git
cd MarkerSfM
python setup.py build
```


## Usage ##
A run script is provided to process the ece_floor4_wall images. This script is located in in `.../scripts` and it is called `run_markersfm.sh`. Note, you should provide the ABSOLUTE PATH to the dataset you want to process. To run the script with the demo data, type:
```
cd scripts
bash run_markersfm.sh ~/ABSOLUTE_PATH_TO/MarkerSfM/data/ece_floor4_wall
```

There are also a bunch of parameters that can be set in the config.yaml file. I suggest that you copy the config.yaml in the project to each data folder you want to process. The main parameter that you definitely want to change is `processes`, which you should set to the number of vcpu's on your machine.


## Data ##
Some demo data is provided with the repository to ensure things are running correctly. All the data from the paper can be downloaded from [here](http://degol2.web.engr.illinois.edu/pages/TagSfM_ECCV18.html).
