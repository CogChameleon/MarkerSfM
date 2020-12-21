#!/bin/bash
# written by joe degol
#
# DESCRIPTION: runs MarkerSfM pipeline on a dataset
#
#
# USAGE: bash run_markersfm.sh <path_to_top_dir>
#
# EXAMPLE: bash run_dataset.sh ~/Documents/Data/statue
#
# NOTES:
# <path_to_top_dir> - this directory needs to have config.yaml and an images directory in it
#

#
# Main
#
# Start of the program
#
bash run_markersfm.sh $1/full
bash run_markersfm.sh $1/half1
bash run_markersfm.sh $1/half2
bash run_markersfm.sh $1/weave1
bash run_markersfm.sh $1/weave2