#!/bin/bash
# written by joe degol
#
# DESCRIPTION: exports two reconstructions to file as a set of correspondences 
# for solving the similarity transformation to align them
#
# SETUP: the relative paths from .../scripts to
#        the executables for MarkerSfM is set here. If
#        the repo changes, this will need to be updated
msfm_path=../bin

#
# USAGE: bash run_export_gdls.sh <path_to_recon1_top_dir>
#
# EXAMPLE: bash run_export_gdls.sh ~/Documents/Data/recon1 ~/Documents/Data/recon2
#
# NOTES:
# <path_to_top_dir> - this directory needs to have config.yaml and an images directory in it
#

#
# RunAndLog <path> <command>
#
# Runs a command and logs it to <path>/run_export_gdls.log
#
function RunAndLog ()
{
    path=$1
    shift
    $@ |& tee -a $path/run_export_gdls.log
}


#
# Main
#
# Start of the program
#
RunAndLog $1 echo '===== Run Export gDLS ====='
RunAndLog $1 echo '= '

RunAndLog $1 $msfm_path/opensfm export_gdls $1

RunAndLog $1 echo '=== End Run Export gDLS ==='
RunAndLog $1 echo ' '
