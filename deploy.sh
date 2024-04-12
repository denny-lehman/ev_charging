#!/bin/bash

# login to the ecr to get pushed docker image
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 241112547949.dkr.ecr.us-east-1.amazonaws.com

docker-compose build --build-arg IMAGE_TAG=$IMAGE
docker-compose up -d 