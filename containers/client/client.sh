#!/bin/sh

WEBSOCKET_PORT=8080

python3 komet.py $WEBSOCKET_PORT  &
sleep 1

# input is in 1MB
INPUT_LENGTH=$(cat /cfg.txt)
python3 criu-client.py localhost:$WEBSOCKET_PORT "$INPUT_LENGTH"
