#!/bin/bash
usage ()
{
  echo 'Usage : docker_shell.sh <container_name>'
  exit
}

if [ "$#" -ne 1 ]
then
    usage
fi

if [ $1 = "web" ]
then
    docker exec -it `docker ps | grep web | awk '{print $1}'` bash
elif [ $1 = "db" ]
then
    docker exec -it `docker ps | grep postgres | awk '{print $1}'` bash
elif [ $1 = "redis" ]
then
    docker exec -it `docker ps | grep redis | awk '{print $1}'` bash
else
    usage
fi