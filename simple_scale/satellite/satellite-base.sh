#!/bin/sh

# install fred
mv /fred /usr/local/bin/fred

apk add --no-cache curl jq

# install docker
apk add --no-cache docker util-linux

# install fuse-overlayfs
apk add --no-cache wget
wget https://github.com/containers/fuse-overlayfs/releases/download/v1.13/fuse-overlayfs-x86_64 -O /usr/bin/fuse-overlayfs
chmod +x /usr/bin/fuse-overlayfs

rc-update add cgroups boot
rc-update add docker default

mkdir -p /etc/docker
cat <<EOF > /etc/docker/daemon.json
{
  "storage-driver": "fuse-overlayfs"
}
EOF

# install tinyfaas
mv /tf-linux-amd64 /usr/local/bin/tf

# install alexandra
mv /alexandra /usr/local/bin/alexandra
chmod +x /usr/local/bin/alexandra
