#!/bin/sh

# install docker
apk add --no-cache util-linux tar docker

# install fuse-overlayfs
apk add --no-cache wget
wget https://github.com/containers/fuse-overlayfs/releases/download/v1.13/fuse-overlayfs-x86_64 -O /usr/bin/fuse-overlayfs
chmod +x /usr/bin/fuse-overlayfs

rc-update add cgroups boot

mkdir -p /etc/docker
cat <<EOF > /etc/docker/daemon.json
{
  "storage-driver": "fuse-overlayfs",
  "experimental": true
}
EOF

apk add podman

# cat <<EOF > /etc/containers/containers.conf
# [containers]
# default_sysctls = [
#  "net.ipv4.ping_group_range=0 0",
# ]
# [network]

# [engine]

# runtime = "runc"

# [engine.runtimes]

# [engine.volume_plugins]
# EOF

# install criu
echo "@testing https://dl-cdn.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories
apk add --no-cache criu@testing
# mv /criu-amd64.bin /usr/local/bin/criu
# chmod +x /usr/local/bin/criu
# criu --version

# install python3
apk add --no-cache python3
apk add --no-cache py3-pip
pip install --upgrade pip
pip install requests flask