#!/bin/bash
# written by joe degol
#
# DESCRIPTION: runs matching between the images of two reconstructions
#
# SETUP: the relative paths from .../scripts to
#        the executables for MarkerSfM is set here. If
#        the repo changes, this will need to be updated
msfm_path=../bin

#
# USAGE: bash run_match_reconstructions.sh <path_to_recon1_top_dir> <path_to_recon2_top_dir>
#
# EXAMPLE: bash run_match_reconstructions.sh ~/Documents/Data/recon1 ~/Documents/Data/recon2
#
# NOTES:
# <path_to_top_dir> - this directory needs to have config.yaml and an images directory in it
#

#
# RunAndLog <path> <command>
#
# Runs a command and logs it to <path>/run_match_reconstructions.log
#
function RunAndLog ()
{
    path=$1
    shift
    $@ |& tee -a $path/run_match_reconstructions.log
}


#
# Main
#
# Start of the program
#
RunAndLog $1 echo '===== Run Match Reconstructions ====='
RunAndLog $1 echo '= '

RunAndLog $1 $msfm_path/opensfm match_reconstructions $1 $2

RunAndLog $1 echo '=== End Run Match Reconstructions ==='
RunAndLog $1 echo ' '
