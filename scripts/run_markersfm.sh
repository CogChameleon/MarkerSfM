#!/bin/bash
# written by joe degol
#
# DESCRIPTION: runs MarkerSfM pipeline on a directory of images
#
# SETUP: the relative paths from .../scripts to
#        the executables for MarkerSfM is set here. If
#        the repo changes, this will need to be updated
msfm_path=../bin

#
# USAGE: bash run_markersfm.sh <path_to_top_dir>
#
# EXAMPLE: bash run_markersfm.sh ~/Documents/Data/ece_floor5_wall
#
# NOTES:
# <path_to_top_dir> - this directory needs to have config.yaml and an images directory in it
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
    $@ |& tee -a $path/log_run_markersfm.log
}


#
# Main
#
# Start of the program
#
RunAndLog $1 echo '===== Run MarkerSFM ====='
RunAndLog $1 echo '= '

RunAndLog $1 echo '= Running MarkerSFM'
RunAndLog $1 $msfm_path/opensfm extract_metadata $1
RunAndLog $1 $msfm_path/opensfm detect_tags $1
RunAndLog $1 $msfm_path/opensfm detect_features $1
RunAndLog $1 $msfm_path/opensfm match_features $1
RunAndLog $1 $msfm_path/opensfm create_tracks $1
RunAndLog $1 $msfm_path/opensfm reconstruct $1
RunAndLog $1 $msfm_path/opensfm mesh $1
RunAndLog $1 $msfm_path/opensfm undistort $1
RunAndLog $1 $msfm_path/opensfm export_ply $1
RunAndLog $1 $msfm_path/export_nvm $1

RunAndLog $1 echo '=== End Run MarkerSFM Script ==='
RunAndLog $1 echo ' '
