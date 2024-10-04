#!/bin/bash

curl -fSL -o firecracker-v1.6.0-x86_64.tgz \
    https://github.com/firecracker-microvm/firecracker/releases/download/v1.6.0/firecracker-v1.6.0-x86_64.tgz
tar -xf firecracker-v1.6.0-x86_64.tgz release-v1.6.0-x86_64/firecracker-v1.6.0-x86_64
mv release-v1.6.0-x86_64/firecracker-v1.6.0-x86_64 firecracker.bin
rm -rf release-v1.6.0-x86_64
rm firecracker-v1.6.0-x86_64.tgz
# sudo mv release-v1.6.0-x86_64/firecracker-v1.6.0-x86_64 ./firecracker.bin

curl -fSL \
    -o vmlinux-5.12.bin \
    "https://tubcloud.tu-berlin.de/s/fcLHfyeQSZwWi5k/download/vmlinux-5.12.bin"
