#!/bin/sh

# install python3
apk add --no-cache python3 curl git py3-pip
python3 -m pip install requests redis websockets
