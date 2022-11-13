#!/bin/bash

echo "stopping xco ..."
sudo initctl emit xco-stop
sleep 1s
echo "stopped!"