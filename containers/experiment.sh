#!/bin/bash

# input: SSH_ADDRESS
SSH_ADDRESS="$1"

# build the image
make client/client.img
make criu/criu.img

# make the trajectory
make traj.zip

rsync -avz "traj.zip" "$SSH_ADDRESS":
rsync -avz "client/client.img" "$SSH_ADDRESS":
rsync -avz "criu/criu.img" "$SSH_ADDRESS":

ssh "$SSH_ADDRESS" sudo rsync client.img /celestial/client.img
ssh "$SSH_ADDRESS" sudo rsync criu.img /celestial/criu.img

# run celestial
NETWORK_INTERFACE=$(ssh "$SSH_ADDRESS" ip route | grep default | awk '{print $5}')
ssh "$SSH_ADDRESS" sudo ./celestial.bin --debug --network-interface="$NETWORK_INTERFACE" > host.log 2>&1 &
sleep 10
ssh "$SSH_ADDRESS" python3 celestial.py traj.zip 127.0.0.1:1969 > coordinator.log 2>&1  &

echo "Running for 15 minutes... (Start time: $(date))"
sleep 910
# sleep 130

# get the results
rsync -avz "$SSH_ADDRESS":/celestial/out/gst-Redmond.out .

# send sigint to celestial coordinator
ssh "$SSH_ADDRESS" sudo kill -2 $(ssh "$SSH_ADDRESS" pgrep -f celestial.py) &> /dev/null || true
sleep 10
ssh "$SSH_ADDRESS" sudo pkill -f python3 || true
ssh "$SSH_ADDRESS" sudo pkill -f celestial.bin || true
