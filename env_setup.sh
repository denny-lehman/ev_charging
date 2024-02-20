#!/bin/bash

ENV_NAME="ev"
echo $ENV_NAME

# conda update conda
echo removing environment $ENV_NAME
conda remove -n $ENV_NAME --all


echo 'Create build environment'
# # See https://github.com/pytorch/vision/issues/7296 for ffmpeg
conda create \
  --name ev \
  --quiet --yes \
  python=3.11 pip

conda activate ev

pip install pandas numpy matplotlib seaborn jupyter psycopg2

pip freeze>requirements.txt
