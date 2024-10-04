#!/bin/sh

podman load -i /redis-alpine-amd64.tar.gz

mkdir -p /mnt/criu
mount -t tmpfs -o size=2G tmpfs /mnt/criu

criu --version

python3 server.py
