#!/bin/sh

echo "starting sensor"

ID="$(curl -s info.celestial/self | jq -r '.identifier.name')"
export ID

echo "Node ID: $ID"

while ! nc -z orchestrator.gst.celestial 8000; do
    echo "waiting for orchestrator.gst.celestial:8000"
    sleep 1
done

chmod +x client.bin
./client.bin "$ID" orchestrator.gst.celestial:8000
