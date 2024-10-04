#!/bin/sh

echo "starting server"

# get IP address
IP_ADDRESS="$(ip addr show eth0 | grep "inet\b" | awk '{print $2}' | cut -d/ -f1)"
export IP_ADDRESS

# get local node ID
ID="$(curl info.celestial/self | jq -r '.identifier.id')"
export ID

SHELL="$(curl info.celestial/self | jq -r '.identifier.shell')"
export SHELL

echo "IP address: $IP_ADDRESS"
echo "Node ID: $ID"
echo "Shell: $SHELL"

# echo "sleeping 10"
# sleep 10

while ! nc -z nase.gst.celestial 2379; do
    echo "waiting for nase.gst.celestial:2379 (etcd)"
    sleep 1
done

chmod +x /usr/local/bin/fred
fred \
    --nodeID "fred-$SHELL-$ID" \
    --nase-host "nase.gst.celestial:2379" \
    --nase-cached \
    --adaptor memory \
    --host 0.0.0.0:9001 \
    --advertise-host "$IP_ADDRESS:9001" \
    --peer-host 0.0.0.0:5555 \
    --peer-advertise-host "$IP_ADDRESS:5555" \
    --log-level error \
    --handler prod \
    --cert /fred.crt \
    --key /fred.key \
    --ca-file /ca.crt \
    --skip-verify \
    --peer-async-replication \
    --peer-cert /fred.crt \
    --peer-key /fred.key \
    --peer-ca /ca.crt \
    --peer-skip-verify \
    --nase-cert /fred.crt \
    --nase-key /fred.key \
    --nase-ca /ca.crt \
    --nase-skip-verify \
    --trigger-cert /fred.crt \
    --trigger-key /fred.key \
    --trigger-ca /fred.crt \
    --trigger-skip-verify \
    --trigger-async \
    2>&1 \
    | sed 's/^/[fred] /' &

while ! nc -z localhost 9001; do
    echo "waiting for localhost:9001 (fred)"
    sleep 1
done

# chmod +x /usr/local/bin/alexandra
# echo "starting alexandra"
# ALEXANDRA_PORT=10000
# alexandra \
#     --address ":${ALEXANDRA_PORT}" \
#     --lighthouse localhost:9001 \
#     --ca-cert /ca.crt \
#     --alexandra-key /client.key \
#     --alexandra-cert /client.crt \
#     --clients-key /client.key \
#     --clients-cert /client.crt \
#     --log-level error \
#     --log-handler prod \
#     --clients-skip-verify \
#     &

# while ! nc -z localhost ${ALEXANDRA_PORT}; do
#     echo "waiting for localhost:${ALEXANDRA_PORT} (alexandra)"
#     sleep 1
# done

# wait for docker ps to work
while ! docker ps; do
    echo "waiting for docker"
    sleep 1
done

echo "starting tinyfaas"
tf &

while true; do
    top -b -n 1 | head -n 20
    for container in $(docker ps -q); do
        echo "Logs for container $container"
        docker logs "$container" --since 11s
    done
    sleep 10
    # top -b -n 1 | head -n 20
done

wait
