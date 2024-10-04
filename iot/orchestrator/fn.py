#!/usr/bin/env python3
import os
import shutil

# this should be illegal
shutil.copy("libstdc++.so.6.0.32", "/usr/lib/libstdc++.so.6.0.32")
os.symlink("/usr/lib/libstdc++.so.6.0.32", "/usr/lib/libstdc++.so.6")
shutil.copy("libgcc_s.so.1", "/usr/lib/libgcc_s.so.1")

import time
import json
import typing
import logging
import threading
import subprocess

import tflite_runtime.interpreter as tflite
import numpy as np
import grpc  # type: ignore
import client_pb2 as client_pb2  # type: ignore
import client_pb2_grpc as client_pb2_grpc  # type: ignore

MODEL_INPUT_LENGTH = 10
KEYGROUP = "sensors"

min_v = 7.8
max_v = 36.0

interpreter = tflite.Interpreter(model_path="./model.tflite")
interpreter.allocate_tensors()

infer = interpreter.get_signature_runner("serving_default")

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


def scale(x: float) -> np.float32:
    if x < min_v:
        return np.float32(0)
    if x > max_v:
        return np.float32(1)
    return np.float32((x - min_v) / (max_v - min_v))


def update_value(name: str, value: float) -> None:
    # update the value in the database
    ur = client_pb2.UpdateRequest(
        keygroup=KEYGROUP,
        id=name,
        data=str(value),
    )

    try:
        stub.Update(ur)

    except Exception as e:
        logging.error(f"Error updating value: {e}")


def get_all_values() -> typing.Dict[str, float]:
    # get all the values from the database
    sr = client_pb2.ScanRequest(
        keygroup=KEYGROUP,
        id="a",
        count=1000,
    )

    try:
        return {item.id: float(item.val) for item in stub.Scan(sr).data}
    except Exception as e:
        logging.error(f"Error scanning values: {e}")

    return {}


def do_inference(values: typing.List[float]) -> float:
    if len(values) < MODEL_INPUT_LENGTH:
        values = values + [0] * (MODEL_INPUT_LENGTH - len(values))

    logging.debug(f"Values: {values}")

    buffer = np.array(values[:10], dtype=np.float32)

    return float(infer(x=buffer)["output_0"][0][0])


def fn(inp: str) -> str:
    # input is a little json
    # {"name": "sensor1", "value", 8.9}

    t1 = time.perf_counter()

    inp = json.loads(inp)

    logging.debug(f"Received value {inp['value']} from {inp['name']}")

    logging.debug("Started update thread")

    # get all the values from fred
    values = get_all_values()

    values[inp["name"]] = inp["value"]

    logging.debug(f"Got values: {values}")

    # in the background, update the value in fred
    threading.Thread(target=update_value, args=(inp["name"], inp["value"])).start()

    # do some inference
    result = do_inference([scale(v) for v in values.values()])

    logging.debug(f"Result: {result}")

    logging.debug(f"Time taken: {time.perf_counter() - t1:.2f}s")

    # return the result
    return str(result)
