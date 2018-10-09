# A script to install dependencies. I tested this with 14.04, 16.04, and 18.04. I do not know if this
# will work with the other versions, but if you follow the comments below, you can figure out what needs
# to be done


# prompt user
echo "This script will install all the dependencies for MarkerSfM. It has been"
echo "successfully tested it with Ubuntu 14.04, 16.04, and 18.04"
echo "Do you wish to continue?"
select yn in "Yes" "No"; do
    case $yn in
        Yes ) break;;
        No ) exit;;
    esac
done

# get ubuntu version
osversion=$( lsb_release -r | awk '{ print $2 }' | sed 's/[.]//' )

# get number of processors
NP=`nproc`

# install common
sudo apt-get update
sudo apt-get install -y git build-essential pkg-config wget unzip
sudo apt-get install -y libatlas-base-dev libsuitesparse-dev libeigen3-dev libgoogle-glog-dev 
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

# install boost. 1.54 for Ubuntu 14.04 and 1.58 for Ubuntu 16.04, 18.04
if [ "$osversion" -eq "1804" ]; then
    echo "deb http://archive.ubuntu.com/ubuntu/ xenial main universe" | sudo tee -a /etc/apt/sources.list
    echo "deb http://archive.ubuntu.com/ubuntu/ xenial-updates main universe" | sudo tee -a /etc/apt/sources.list
    sudo apt-get update
    sudo apt-get install -y aptitude
    sudo aptitude install -y libboost1.58-all-dev
    sudo aptitude install -y libboost-python1.58-dev
    sudo aptitude install -y libboost1.58-all-dev
else
    sudo apt-get install -y libboost-all-dev libboost-python-dev
fi

# move to Downloads directory
mkdir -p ~/Downloads
cd ~/Downloads

# cmake, for 14.04 the version is too low from apt
if [ "$osversion" -eq "1404" ]; then
    cd ~/Downloads
    wget https://cmake.org/files/v3.5/cmake-3.5.2.tar.gz
    tar xzvf cmake-3.5.2.tar.gz
    cd cmake-3.5.2/
    ./bootstrap
    make -j$NP
    sudo make install
    export PATH=$PATH:/usr/local/bin
else
    sudo apt-get install -y cmake
fi

# opencv
sudo apt-get install -y libgtk2.0-dev libavcodec-dev libavformat-dev libswscale-dev libtbb2 libtbb-dev libjpeg-dev libpng-dev libtiff-dev libjasper-dev libdc1394-22-dev
wget https://github.com/opencv/opencv/archive/3.4.3.zip
unzip 3.4.3.zip
cd opencv-3.4.3
mkdir build
cd build
cmake -D CMAKE_BUILD_TYPE=Release -D CMAKE_INSTALL_PREFIX=/usr/local ..
make -j$NP
sudo make install

# ceres
cd ~/Downloads
wget http://ceres-solver.org/ceres-solver-1.10.0.tar.gz
tar xvzf ceres-solver-1.10.0.tar.gz
cd ceres-solver-1.10.0
mkdir build
cd build
cmake .. -DCMAKE_C_FLAGS="-fPIC -Wno-maybe-uninitialized" -DCMAKE_CXX_FLAGS="-fPIC -Wno-maybe-uninitialized" -DBUILD_EXAMPLES=OFF -DBUILD_TESTING=OFF
make -j$NP
sudo make install

# opengv
cd ~/Downloads
git clone https://github.com/paulinus/opengv.git
cd opengv
mkdir build
cd build
cmake .. -DBUILD_TESTS=OFF -DBUILD_PYTHON=ON
make -j$NP
sudo make install
