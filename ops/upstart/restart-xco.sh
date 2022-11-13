#!/bin/bash

echo "stopping xco ..."
sudo initctl emit xco-stop
sleep 1s
echo "starting xco ..."
sudo initctl emit xco-start
touch /tmp/django-restart
echo "restart complete!"