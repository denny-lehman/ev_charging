#!/bin/bash

# login to the ecr to get pushed docker image
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 241112547949.dkr.ecr.us-east-1.amazonaws.com

# copy all nginx files to the /etc/nginx directory
sudo mkdir -p /etc/nginx/conf.d && sudo mv nginx.conf /etc/nginx/ && sudo mv conf.d/project.conf /etc/nginx/conf.d/

docker-compose up --build -d