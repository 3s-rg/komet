#!/bin/bash

set -ex

# input: SSH_ADDRESS INTERNAL_SSH_ADDRESS
read -r -a SSH_ADDRESSES <<< "$1"
read -r -a INTERNAL_SSH_ADDRESSES <<< "$2"

# build the image
# make client/client.img
# make satellite/satellite.img
# make orchestrator/orchestrator.img
# make nameservice/nase.img
# make origin/origin.img

make all

# TRAJ_FILE="traj-smaller.zip"
TRAJ_FILE="traj.zip"

# make the trajectory
make "$TRAJ_FILE"

upload_images() {
    local SSH_ADDRESS=$1
    rsync -avz "$TRAJ_FILE" "$SSH_ADDRESS":
    rsync -avz "client/client.img" "$SSH_ADDRESS":
    rsync -avz "satellite/satellite.img" "$SSH_ADDRESS":
    rsync -avz "orchestrator/orchestrator.img" "$SSH_ADDRESS":
    rsync -avz "nameservice/nase.img" "$SSH_ADDRESS":
    rsync -avz "origin/origin.img" "$SSH_ADDRESS":

    ssh "$SSH_ADDRESS" sudo rsync client.img /celestial/client.img
    ssh "$SSH_ADDRESS" sudo rsync satellite.img /celestial/satellite.img
    ssh "$SSH_ADDRESS" sudo rsync orchestrator.img /celestial/orchestrator.img
    ssh "$SSH_ADDRESS" sudo rsync nase.img /celestial/nase.img
    ssh "$SSH_ADDRESS" sudo rsync origin.img /celestial/origin.img
}

for SSH_ADDRESS in "${SSH_ADDRESSES[@]}"; do
    upload_images "$SSH_ADDRESS" &
done
wait

for SSH_ADDRESS in "${SSH_ADDRESSES[@]}"; do
    # run celestial
    NETWORK_INTERFACE=$(ssh "$SSH_ADDRESS" ip route | grep default | awk '{print $5}')
    ssh "$SSH_ADDRESS" sudo ./celestial.bin --debug --network-interface="$NETWORK_INTERFACE" > "host-$SSH_ADDRESS".log 2>&1 &
done
sleep 10

COORDINATOR_ADDRESS="${SSH_ADDRESSES[0]}"
HOSTS=""

for INTERNAL_SSH_ADDRESS in "${INTERNAL_SSH_ADDRESSES[@]}"; do
    HOSTS="$HOSTS $INTERNAL_SSH_ADDRESS:1969"
done

ssh "$COORDINATOR_ADDRESS" python3 celestial.py "$TRAJ_FILE" $HOSTS > coordinator.log 2>&1  &

echo "Running for 15 minutes... (Start time: $(date))"
# sleep 610
# sleep 910
# sleep 300
sleep 1510
# sleep 180

rm -rf out/*
get_results() {
    local SSH_ADDRESS=$1
    # get the results
    rsync -avz "$SSH_ADDRESS":/celestial/out/*.out out/
}

for SSH_ADDRESS in "${SSH_ADDRESSES[@]}"; do
    get_results "$SSH_ADDRESS"
done
# wait

# send sigint to celestial coordinator
ssh "$COORDINATOR_ADDRESS" sudo kill -2 "$(ssh "$COORDINATOR_ADDRESS" pgrep -f celestial.py)" || true
sleep 10

for SSH_ADDRESS in "${SSH_ADDRESSES[@]}"; do
    ssh "$SSH_ADDRESS" sudo pkill -f python3
    ssh "$SSH_ADDRESS" sudo pkill -f celestial.bin
done
