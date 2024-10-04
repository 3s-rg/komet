#!/usr/bin/env python3
import time
import json
import logging
import subprocess

import grpc  # type: ignore
import client_pb2 as client_pb2  # type: ignore
import client_pb2_grpc as client_pb2_grpc  # type: ignore

KEYGROUP = "simple"

with open("cert.crt") as f:
    crt = f.read().encode()

with open("cert.key") as f:
    key = f.read().encode()

with open("ca.crt") as f:
    ca = f.read().encode()

creds = grpc.ssl_channel_credentials(ca, key, crt)

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(message)s")


def get_gateway_ip():
    try:
        # Run the "ip route" command and capture its output
        result = subprocess.run(["ip", "route"], capture_output=True, text=True)
        output = result.stdout

        # Find the line containing "default via", which indicates the default gateway
        default_route_line = next(
            line for line in output.split("\n") if "default via" in line
        )

        # Extract the gateway IP address from the line
        gateway_ip = default_route_line.split(" ")[2]
        return gateway_ip
    except Exception as e:
        print("An error occurred:", e)
        return None


gateway = get_gateway_ip()
print(f"Gateway IP: {gateway}")

stub = client_pb2_grpc.ClientStub(
    grpc.secure_channel(
        f"{gateway}:9001",
        creds,
        options=(("grpc.ssl_target_name_override", "localhost"),),
    )
)


def put(key: str, value: str) -> None:
    ur = client_pb2.UpdateRequest(
        keygroup=KEYGROUP,
        id=key,
        data=str(value),
    )

    stub.Update(ur)


def fn(inp: str) -> str:
    # input is a little json
    # {"key": "sensor1", "value", 8.9}

    t1 = time.perf_counter()

    inp = json.loads(inp)

    logging.debug(f"Received value {inp['value']} for key {inp['key']}")

    try:
        put(inp["key"], inp["value"])
    except Exception as e:
        logging.error(f"Error putting value: {e}")

    logging.debug(f"Time taken: {time.perf_counter() - t1}s")

    return "OK"
