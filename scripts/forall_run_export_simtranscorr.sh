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
# USAGE: bash run_export_simtranscorr.sh <path_to_recon1_top_dir> <path_to_recon2_top_dir>
#
# EXAMPLE: bash run_export_simtranscorr.sh ~/Documents/Data/recon1 ~/Documents/Data/recon2
#
# NOTES:
# <path_to_top_dir> - this directory needs to have config.yaml and an images directory in it
#



#
# Main
#
# Start of the program
#

# for each directory
for dir in $1/*; do
    if [ -d "$dir" ]; then
        echo ":::::::::: $dir ::::::::::"
        bash run_export_simtranscorr.sh "$dir/half1" "$dir/half2"
        bash run_export_simtranscorr.sh "$dir/weave1" "$dir/weave2"
    fi
done
