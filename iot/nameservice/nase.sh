#!/bin/sh

echo "starting nameservice"

# get IP address
export IP_ADDRESS=$(ip addr show eth0 | grep "inet\b" | awk '{print $2}' | cut -d/ -f1)

chmod +x /usr/local/bin/etcd
etcd --name s-1 \
    --data-dir /tmp/etcd/s-1 \
    --listen-client-urls https://${IP_ADDRESS}:2379 \
    --advertise-client-urls https://${IP_ADDRESS}:2379 \
    --listen-peer-urls http://${IP_ADDRESS}:2380 \
    --initial-advertise-peer-urls http://${IP_ADDRESS}:2380 \
    --initial-cluster s-1=http://${IP_ADDRESS}:2380 \
    --initial-cluster-token tkn \
    --initial-cluster-state new \
    --cert-file=/nase.crt \
    --key-file=/nase.key \
    --client-cert-auth \
    --trusted-ca-file=/ca.crt
