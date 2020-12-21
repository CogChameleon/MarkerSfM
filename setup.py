#!/usr/bin/env python

from distutils.core import setup
import sys
import os
import errno
import subprocess


def mkdir_p(path):
    '''Make a directory including parent directories.
    '''
    try:
        os.makedirs(path)
    except os.error as exc:
        if exc.errno != errno.EEXIST or not os.path.isdir(path):
            raise

print("Configuring...")
mkdir_p('cmake_build')
subprocess.Popen(['cmake','../opensfm/src'], cwd='cmake_build').wait()

print("Compiling extension...")
subprocess.Popen(['make','-j4'], cwd='cmake_build').wait()

print("Building package")
setup(
    name='MarkerSfM',
    version='1.0',
    description='Improved Structure from Motion Using Fiducial Marker Matching',
    url='https://github.com/CogChameleon/MarkerSfM.git',
    author='Joseph DeGol',
    license='BSD 2-Clause',
    packages=['opensfm', 'opensfm.commands'],
    scripts=['bin/opensfm_run_all', 'bin/opensfm'],
    package_data={
        'opensfm': ['csfm.so', 'data/sensor_data.json']
    },
)
