#!/bin/sh

# install python3
apk add --no-cache python3 curl git py3-pip gcc musl-dev python3-dev build-base linux-headers
python3 -m pip install websockets grpcio==1.56.0 protobuf==4.23.3
