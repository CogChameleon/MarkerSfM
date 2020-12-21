#!/bin/bash
# written by joe degol
#
# DESCRIPTION: scales a completed reconstruction using detected marker sizes
#
# SETUP: the relative paths from .../scripts to
#        the executables for MarkerSfM is set here. If
#        the repo changes, this will need to be updated
msfm_path=../bin

#
# USAGE: bash run_scalesfm.sh <path_to_top_dir>
#
# EXAMPLE: bash run_scalesfm.sh ~/Documents/Data/ece_floor5_wall
#
# NOTES:
# <path_to_top_dir> - this directory needs to have been processed by run_markersfm.sh or some equivalent
#

#
# RunAndLog <path> <command>
#
# Runs a command and logs it to <path>/run_markersfm.log
#
function RunAndLog ()
{
    path=$1
    shift
    $@ |& tee -a $path/log_run_scalesfm.log
}


#
# Main
#
# Start of the program
#
RunAndLog $1 echo '===== Run ScaleSFM ====='
RunAndLog $1 echo '= '

cp $1/reconstruction.json $1/reconstruction.noscale.json
RunAndLog $1 $msfm_path/opensfm tag_scale $1
RunAndLog $1 $msfm_path/opensfm mesh $1
RunAndLog $1 $msfm_path/opensfm undistort $1
RunAndLog $1 $msfm_path/opensfm export_ply $1

RunAndLog $1 echo '=== End Run ScaleSFM ==='
RunAndLog $1 echo ' '
