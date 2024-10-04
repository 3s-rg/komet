#!/bin/bash

set -xe

# input:
# 1: gcloud or ip
# 2: experiment dir
EXPERIMENT_DIR="$2"

# check that there are two arguments
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <ip or gcloud> <experiment_dir>"
    exit 1
fi

if [ -z "$EXPERIMENT_DIR" ]; then
    echo "Usage: $0 <ip or gcloud> <experiment_dir>"
    exit 1
fi

# check that directory exists
if [ ! -d "$EXPERIMENT_DIR" ]; then
    echo "Directory $EXPERIMENT_DIR does not exist"
    exit 1
fi

NUM_GCLOUD_HOSTS=16

# make the infrastructure if we use gcloud
if [ "$1" == "gcloud" ]; then
    tofu init
    tofu apply -auto-approve -var "host_count=$NUM_GCLOUD_HOSTS"

    GCP_PROJECT="$(tofu output -json | jq -r '.project.value')"

    gcloud config set project "$GCP_PROJECT"
    gcloud compute config-ssh

    SSH_ADDRESSES=()
    for ((i=0;i<NUM_GCLOUD_HOSTS;i++)); do
        SSH_ADDRESSES+=("$(tofu output -json | jq -r ".host_name.value[$i]")")
    done

    # restart the machines
    for GCP_INSTANCE in "${SSH_ADDRESSES[@]}"; do
        # ssh-keyscan -H "$GCP_INSTANCE" >> ~/.ssh/known_hosts
        yes | ssh -o ConnectTimeout=1 "$GCP_INSTANCE" sudo reboot now || true
    done

    sleep 1

    INTERNAL_SSH_ADDRESSES=()
    for ((i=0;i<NUM_GCLOUD_HOSTS;i++)); do
        INTERNAL_SSH_ADDRESSES+=("$(tofu output -json | jq -r ".host_ip_internal.value[$i]")")
    done

else
    # split by comma
    IFS=',' read -r -a SSH_ADDRESSES <<< "$1"
    printf '%s\n' "${SSH_ADDRESSES[@]}"

    # at least reboot the machine
    for SSH_ADDRESS in "${SSH_ADDRESSES[@]}"; do
        # ssh-keyscan -H "$SSH_ADDRESS" >> ~/.ssh/known_hosts
        ssh "$SSH_ADDRESS" sudo reboot now || true
    done

    INTERNAL_SSH_ADDRESSES=("${SSH_ADDRESSES[@]}")
fi

for SSH_ADDRESS in "${SSH_ADDRESSES[@]}"; do
    until ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$SSH_ADDRESS" echo
    do
        echo "host instance not ready yet"
        sleep 5
        if [ "$1" == "gcloud" ]; then
            # make sure we have the right config
            gcloud compute config-ssh
        fi
    done
done

deploy_celestial() {
    local SSH_ADDRESS="$1"
    sleep 5
    ssh "$SSH_ADDRESS" sudo apt-get update
    ssh "$SSH_ADDRESS" sudo apt-get install \
        --no-install-recommends \
        --no-install-suggests \
        -y \
        rsync \
        python3 \
        python3-pip \
        python3-dev \
        g++ \
        gcc \
        make \
        cmake \
        build-essential \
        wireguard \
        ipset

    if ! ssh "$SSH_ADDRESS" test -d celestial-git; then
        ssh "$SSH_ADDRESS" git clone https://github.com/OpenFogStack/celestial.git celestial-git
    else
        ssh "$SSH_ADDRESS" git -C celestial-git pull
    fi

    ssh "$SSH_ADDRESS" cp celestial-git/celestial.py .
    ssh "$SSH_ADDRESS" cp celestial-git/requirements.txt .
    ssh "$SSH_ADDRESS" cp -r celestial-git/celestial .
    ssh "$SSH_ADDRESS" cp -r celestial-git/proto .

    ssh "$SSH_ADDRESS" sudo mkdir -p /celestial

    rsync -avz "vmlinux-5.12.bin" "$SSH_ADDRESS":
    rsync -avz "vmlinux-5.15-containerd.bin" "$SSH_ADDRESS":
    rsync -avz "firecracker.bin" "$SSH_ADDRESS":
    rsync -avz "celestial.bin" "$SSH_ADDRESS":

    # prepare the instance
    ssh "$SSH_ADDRESS" pip install pip -U
    ssh "$SSH_ADDRESS" pip install -r requirements.txt

    ssh "$SSH_ADDRESS" sudo rm /celestial/ce*.img || true

    ssh "$SSH_ADDRESS" sudo rsync firecracker.bin /usr/local/bin/firecracker
    ssh "$SSH_ADDRESS" sudo rsync vmlinux-5.12.bin /celestial/vmlinux-5.12.bin
    ssh "$SSH_ADDRESS" sudo rsync vmlinux-5.15-containerd.bin /celestial/vmlinux-5.15-containerd.bin

    ssh "$SSH_ADDRESS" sudo rm -rf /celestial/out/* || true

    # set up swap on the instance
    # about 64GB of swap is good
    # this is mostly for suspended instances
    ssh "$SSH_ADDRESS" sudo fallocate -l 64G /swapfile
    ssh "$SSH_ADDRESS" sudo chmod 600 /swapfile
    ssh "$SSH_ADDRESS" sudo mkswap /swapfile
    ssh "$SSH_ADDRESS" sudo swapon /swapfile
}

for SSH_ADDRESS in "${SSH_ADDRESSES[@]}"; do
    deploy_celestial "$SSH_ADDRESS" &
done

wait

# if there is only one instance, use 127.0.0.1 as internal address
if [ "${#INTERNAL_SSH_ADDRESSES[@]}" -eq 1 ]; then
    INTERNAL_SSH_ADDRESSES=( "127.0.0.1" )
fi

pushd "$EXPERIMENT_DIR"
bash "experiment.sh" "${SSH_ADDRESSES[*]}" "${INTERNAL_SSH_ADDRESSES[*]}"
