# A script to install dependencies. I tested this with 18.04. I suspect it will work in 16.04 also.
# If you run this with 14.04, you will need to uninstall cmake and build an updated version (as outlined)
# in the README.md


# prompt user
echo "This script will install all the dependencies for MarkerSfM. It has been"
echo "successfully tested it with Ubuntu 14.04 and 16.04"
echo "Do you wish to continue?"
select yn in "Yes" "No"; do
    case $yn in
        Yes ) break;;
        No ) exit;;
    esac
done


# install common
sudo apt-get update
sudo apt-get install -y git build-essential cmake pkg-config wget unzip
sudo apt-get install -y libatlas-base-dev libboost-all-dev libboost-python-dev libsuitesparse-dev libeigen3-dev libgoogle-glog-dev 
sudo apt-get install -y python-dev python-numpy python-pip python-pyexiv2 python-pyproj python-scipy
sudo pip install --upgrade pip
sudo pip install exifread==2.1.2
sudo pip install gpxpy==1.1.2
sudo pip install networkx==1.11
sudo pip install pyproj==1.9.5.1
sudo pip install pytest==3.0.7
sudo pip install python-dateutil==2.6.0
sudo pip install PyYAML==3.12
sudo pip install xmltodict==0.10.2

# move to Downloads directory
mkdir -p ~/Downloads
cd ~/Downloads

# opencv
sudo apt-get install -y libgtk2.0-dev libavcodec-dev libavformat-dev libswscale-dev libtbb2 libtbb-dev libjpeg-dev libpng-dev libtiff-dev libjasper-dev libdc1394-22-dev
wget https://github.com/opencv/opencv/archive/3.4.3.zip
unzip 3.4.3.zip
cd opencv-3.4.3
mkdir build
cd build
cmake -D CMAKE_BUILD_TYPE=Release -D CMAKE_INSTALL_PREFIX=/usr/local ..
make -j
sudo make install

# ceres
cd ~/Downloads
wget http://ceres-solver.org/ceres-solver-1.10.0.tar.gz
tar xvzf ceres-solver-1.10.0.tar.gz
cd ceres-solver-1.10.0
mkdir build
cd build
cmake .. -DCMAKE_C_FLAGS=-fPIC -DCMAKE_CXX_FLAGS=-fPIC -DBUILD_EXAMPLES=OFF -DBUILD_TESTING=OFF
make -j
sudo make install

# opengv
cd ~/Downloads
git clone https://github.com/paulinus/opengv.git
cd opengv
mkdir build
cd build
cmake .. -DBUILD_TESTS=OFF -DBUILD_PYTHON=ON
make -j
sudo make install