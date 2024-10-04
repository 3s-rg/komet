#!/usr/bin/env python3

# on import, set up the database connection
import urllib.request
import subprocess
import threading
import logging
import os
import typing
import time
import random

import grpc  # type: ignore
import requests  # type: ignore

# import middleware_pb2 as middleware_pb2  # type: ignore
# import middleware_pb2_grpc as middleware_pb2_grpc  # type: ignore
import client_pb2 as client_pb2  # type: ignore
import client_pb2_grpc as client_pb2_grpc  # type: ignore

# ORIGIN_ADDR = "origin.gst.celestial"
ORIGIN_ADDR = "10.0.0.6"
DELETION_LIKELIHOOD = (
    0.01  # arbitrary value, but we want to keep a max of about 100 values
)
REQUEST_SESSION = requests.Session()


with open("cert.crt") as f:
    crt = f.read().encode()

with open("cert.key") as f:
    key = f.read().encode()

with open("ca.crt") as f:
    ca = f.read().encode()

creds = grpc.ssl_channel_credentials(ca, key, crt)

logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(message)s")


def logflush() -> None:
    for handler in logging.getLogger().handlers:
        handler.flush()


# connect to the gateway
def get_ip_and_gateway() -> typing.Tuple[str, str]:
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

        # Find the line containing "src", which indicates the local IP address
        local_ip_line = next(line for line in output.split("\n") if "src" in line)

        # Extract the local IP address from the line
        ip = local_ip_line.split(" ")[7]

        # logging.debug(f"IP: {ip}, Gateway IP: {gateway_ip}, output: {output}")
        return ip, gateway_ip
    except Exception as e:
        print("An error occurred:", e)
        os.exit(1)


# def get_id() -> str:
#     try:
#         r = requests.get("http://info.celestial/self")

#         if r.status_code != 200:
#             logging.error(f"Failed to get id: {r.text}")
#             return ""

#         return str(r.json()["identifier"]["id"])

#     except Exception as e:
#         logging.error(f"Failed to get id, error: {e}")

#     return ""


ip, gateway = get_ip_and_gateway()
print(f"IP: {ip}")
print(f"Gateway IP: {gateway}")

# can't get the ID from within the function container
# because docker sucks
# the host is defined on the host machine but the container
# does not inherit that
# id = get_id()

# random.seed(ip + id)
sat_id = os.getenv("SATID", "")
print(f"ID: {sat_id}")
random.seed(sat_id + ip)

# stub = middleware_pb2_grpc.MiddlewareStub(
#     grpc.secure_channel(
#         f"{gateway}:10000",
#         creds,
#     )
# )
channel = grpc.secure_channel(
    f"{gateway}:9001",
    creds,
    options=(("grpc.ssl_target_name_override", "localhost"),),
)


def path_to_id(path: str) -> str:
    # replace everything thats not alphanumeric to x
    # this is a hack, obviously. base64 encoding would be better but is harder to debug
    return "".join([c if c.isalnum() else "x" for c in path])


def fn(path: str) -> str:
    stub = client_pb2_grpc.ClientStub(channel)

    # log this request
    # logging.flush()
    try:
        logflush()
    except Exception as e:
        print(f"Failed to flush logs: {e}", flush=True)

    def append_to_log(path: str) -> None:
        # logging.flush()
        logflush()
        logging.debug(f"Appending {path} to log")
        ar = client_pb2.AppendRequest()

        ar.keygroup = "log"
        ar.id = time.time_ns()
        ar.data = path

        try:
            stub.Append(ar)
            logging.debug(f"Appended {path} to log")
        except Exception as e:
            logging.error(f"Failed to append to log: {e}")

        # with a 0.9% chance, trigger deleting old items
        r = random.random()
        if r > DELETION_LIKELIHOOD:
            logging.debug(f"not deleting old items ({r})")
            return

        logging.info("Triggering deletion of old items")
        try:
            request = urllib.request.Request(
                f"http://{gateway}:8000/cdndelete", method="POST"
            )
            with urllib.request.urlopen(request) as response:
                _ = response.read().decode("utf-8")
            logging.info("Deleted old items")
        except Exception:
            logging.error(f"Failed to delete old items: {r.text}")

    threading.Thread(target=append_to_log, args=(path_to_id(path),)).start()

    logging.info(f"starting fn call for {path}")

    try:
        # check if path is in the database
        # r = middleware_pb2.ReadRequest()  # type: ignore
        t1 = time.perf_counter()

        r = client_pb2.ReadRequest()

        r.keygroup = "cdn"
        r.id = path_to_id(path)

        data = stub.Read(r, timeout=1)

        t2 = time.perf_counter()

        logging.info(f"Read took {t2 - t1} seconds ({path})")

        if len(data.data) > 0:
            logging.info(f"Cache hit for {path}")
            return f"{data.data[0].val}1"
    except Exception as e:
        # probably not in the database
        logging.debug(f"Cache miss for {path} ({path}): {e}")
        # pass

    t3 = time.perf_counter()
    # if not, get it from origin
    try:
        # r = requests.get(, timeout=1)
        # r = urllib.request.urlopen(f"http://{ORIGIN_ADDR}:8000" + path, timeout=1)
        r = REQUEST_SESSION.get(f"http://{ORIGIN_ADDR}:8000" + path, timeout=1)

    except Exception as e:
        logging.error(f"Failed to get key {path}: {e}")
        raise e

    t4 = time.perf_counter()

    logging.info(f"Origin took {t4 - t3} ({path})")

    data = r.text
    # r.close()

    t5 = time.perf_counter()

    logging.info(f"Read data in {t5 - t4} seconds ({path})")

    # data = data.decode("utf-8")

    t6 = time.perf_counter()

    logging.info(f"Decoded data in {t6 - t5} seconds ({path})")

    # then put it in database (in the background)
    # data = r.content.decode("utf-8")

    def update_in_store(data: str, path: str) -> None:
        r = client_pb2.UpdateRequest(
            keygroup="cdn",
            id=path_to_id(path),
            data=data,
        )  # type: ignore

        try:
            stub.Update(r)
            logging.info(f"Updated {path} in store")
        except Exception as e:
            logging.error(f"Failed to update {path} in store: {e}")

    threading.Thread(
        target=update_in_store,
        args=(
            data,
            path,
        ),
    ).start()

    # return the data

    t7 = time.perf_counter()
    logging.info(f"Started thread in {t7 - t6} seconds ({path})")
    logging.info(f"Returning data in {t7 - t1} seconds ({path})")
    return f"{data}0"
