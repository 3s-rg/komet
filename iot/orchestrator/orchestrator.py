#!/usr/bin/env python

import concurrent.futures as concurrent_futures
import logging
import sys
import typing
import queue
import threading
import time
import base64
import socket
from dataclasses import dataclass
import urllib.request
import json
import math

import websockets.sync.server  # type: ignore
import grpc  # type: ignore
import psutil

import client_pb2 as client_pb2  # type: ignore
import client_pb2_grpc as client_pb2_grpc  # type: ignore

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s:%(levelname)s:%(filename)s: %(message)s"
)

# simple approach to prevent starvation at the beginning
ENDPOINT = "sensors"

GROUNDSTATION_PREFIX = "sensor"

# convert it to base64
with open("fn.zip", "rb") as fi:
    f1data = fi.read()
encodedf1 = base64.b64encode(f1data).decode("utf-8")


@dataclass
class Sat:
    group: int
    id: int

    def hostname(self) -> str:
        return f"{self.id}.{self.group}.celestial"

    def fred(self) -> str:
        return f"fred-{self.group}-{self.id}"

    def __hash__(self) -> int:
        return hash((self.group, self.id))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Sat):
            return False
        return self.group == other.group and self.id == other.id

    def __str__(self) -> str:
        return f"{self.group}-{self.id}"


def get_channel(host: str) -> client_pb2_grpc.ClientStub:
    with open("client.crt") as f:
        crt = f.read().encode()

    with open("client.key") as f:
        key = f.read().encode()

    with open("ca.crt") as f:
        ca = f.read().encode()

    creds = grpc.ssl_channel_credentials(ca, key, crt)

    return client_pb2_grpc.ClientStub(
        grpc.secure_channel(
            host,
            creds,
            # options=(("grpc.tls_skip_hostname_check", 1),),
            options=(("grpc.ssl_target_name_override", "localhost"),),
        )
    )


def deploy_functions(new_sat: Sat, deployed_sat: typing.Optional[Sat]) -> None:
    t1 = time.perf_counter()

    # wait for the sat to be available
    # sometimes this takes a bit of time at the beginning of an experiment
    # while ! nc -z localhost 9001
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as so:
            try:
                so.connect((new_sat.hostname(), 9001))
                break
            except Exception:
                print(f"Waiting for {new_sat} to be available")
                time.sleep(0.5)

    t2 = time.perf_counter()
    logging.info(f"Sats are available in {t2 - t1}")

    # if there is no sat yet, we have to create the keygroup
    if deployed_sat is None:
        # create keygroup
        logging.info(f"Creating keygroups for {new_sat}")
        r = client_pb2.CreateKeygroupRequest()  # type: ignore

        r.keygroup = ENDPOINT
        r.mutable = True
        r.expiry = 0

        stub = get_channel(f"{new_sat.hostname()}:9001")
        stub.CreateKeygroup(r)

        r = client_pb2.UpdateRequest()  # type: ignore

        r.keygroup = ENDPOINT
        r.id = "a"
        r.data = "0"

        stub.Update(r)

        t3 = time.perf_counter()
        logging.info(f"Created keygroup in {t3 - t2}")

    else:
        try:
            # t3 = time.perf_counter()
            # if closest_sat is None, we are the first sat
            logging.info(f"Replicating data from {deployed_sat} to {new_sat}")
            # replicate the data from the closest sat
            r = client_pb2.AddReplicaRequest()  # type: ignore

            r.keygroup = ENDPOINT
            r.nodeId = new_sat.fred()

            stub = get_channel(f"{deployed_sat.hostname()}:9001")

            stub.AddReplica(r)

            # t4 = time.perf_counter()
            # logging.info(f"Replicated data to {sat} in {t4 - t3}")
        except Exception as e:
            logging.error(f"Failed to replicate data to {new_sat}: {e}")

            try:
                path_data = urllib.request.urlopen(
                    f"http://info.celestial/path/{deployed_sat.group}/{deployed_sat.id}/{new_sat.group}/{new_sat.id}"
                ).read()

                path_data = json.loads(path_data)

            except Exception as e:
                logging.error(f"Failed to get path data: {e}")

            logging.info(f"Path data: {path_data}")

        t3 = time.perf_counter()
        logging.info(f"Replicated data in {t3 - t2}")

    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as so:
            try:
                so.connect((new_sat.hostname(), 8080))
                break
            except (ConnectionRefusedError, socket.timeout):
                print(f"Waiting for {new_sat} to be available")
                time.sleep(0.5)

    t4 = time.perf_counter()
    logging.info(f"Sats are available in {t4 - t3}")

    logging.info(f"Starting functions on {new_sat}")

    try:
        r = urllib.request.urlopen(
            f"http://{new_sat.hostname()}:8080/upload",
            data=json.dumps(
                {
                    "name": ENDPOINT,
                    "zip": encodedf1,
                    "threads": 8,
                    "env": "python3",
                    "envs": [f"SATID={str(new_sat)}"],
                }
            ).encode("utf-8"),
        )

        if r.status != 200:
            logging.error(f"Failed to start function: {r.read()}")

    except Exception as e:
        logging.error(f"Failed to start function: {e}")

    t5 = time.perf_counter()
    logging.info(f"Deployed functions in {t5 - t4}")

    logging.info(f"Deployed functions in {time.perf_counter() - t1}")


def remove_function(sat: Sat) -> None:
    t1 = time.perf_counter()

    logging.info(f"Removing function from {sat}")

    # remove the function
    def _delete_function(fn: str) -> None:
        try:
            r = urllib.request.urlopen(
                f"http://{sat.hostname()}:8080/delete",
                data=json.dumps({"name": fn}).encode("utf-8"),
                timeout=1,
            )

            if r.status != 200:
                logging.error(f"Failed to remove function {fn}: {r.read()}")

        except Exception as e:
            logging.error(f"Failed to remove function: {e}")

    thread1 = threading.Thread(target=_delete_function, args=(ENDPOINT,))

    thread1.start()

    # in the mean time, check that the sat is even available anymore
    try:
        r = urllib.request.urlopen(
            f"http://info.celestial/shell/{sat.group}/{sat.id}", timeout=1
        ).read()

        r = json.loads(r)

        logging.info(f"checking {sat} got response: {r}")

        if not r["active"]:
            logging.info(
                f"Sat {sat} is not active anymore, skipping deletion (good luck!)"
            )
            return
    except Exception as e:
        logging.error(f"Failed to check if sat is active: {e}")

    thread1.join()

    t2 = time.perf_counter()
    logging.info(f"Removed functions from {sat} in {t2 - t1}")

    logging.info(f"Removing keygroup from {sat}")

    # unreplicate the data
    def _remove_keygroup(kg: str) -> None:
        try:
            rrr = client_pb2.RemoveReplicaRequest()  # type: ignore

            rrr.keygroup = kg
            rrr.nodeId = sat.fred()

            stub = get_channel(f"{sat.hostname()}:9001")

            stub.RemoveReplica(rrr)
        except Exception as e:
            logging.error(f"Failed to unreplicate data from {sat}: {e}")
            # assume it worked?

    thread1 = threading.Thread(target=_remove_keygroup, args=(ENDPOINT,))

    thread1.start()

    thread1.join()

    t3 = time.perf_counter()
    logging.info(f"Removed keygroups from {sat} in {t3 - t2}")


@dataclass
class Groundstation:
    name: str
    update_queue: queue.SimpleQueue[Sat]

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Groundstation):
            return False
        return self.name == other.name


class Constellation:
    def __init__(self) -> None:
        self.deployed_sat = None
        self.groundstations: typing.List[Groundstation] = []
        self.lock = threading.Lock()
        self.num_groundstation = self.get_num_groundstations()

    def get_num_groundstations(self) -> int:
        try:
            r = urllib.request.urlopen("http://info.celestial/info").read()
            r = json.loads(r)

            return len(
                list(
                    filter(
                        lambda x: x["identifier"]["name"].startswith(
                            GROUNDSTATION_PREFIX
                        ),
                        r["groundstations"],
                    )
                )
            )
        except Exception as e:
            logging.error(f"Failed to get number of groundstations: {e}")
            exit(1)

    def add_groundstation(self, id: str) -> queue.SimpleQueue[Sat]:
        with self.lock:
            return self._add_groundstation(id)

    def _add_groundstation(self, id: str) -> queue.SimpleQueue[Sat]:
        update_queue = queue.SimpleQueue()  # type: ignore
        self.groundstations.append(Groundstation(id, update_queue))
        return update_queue

    def update_sats(self) -> None:
        with self.lock:
            l_gst = len(self.groundstations)
        if l_gst < self.num_groundstation:
            logging.info(
                f"Waiting for all groundstations to connect (have {l_gst} / {self.num_groundstation})"
            )
            time.sleep(0.1)
            return

        with self.lock:
            self._update_sats()

    def _update_sats(self) -> None:
        def get_distance(gst: Groundstation, s: Sat) -> typing.Optional[int]:
            # get the distance
            # logging.info(f"Getting path data for {s} to {gst.name}")
            # t1 = time.perf_counter()

            path_data = urllib.request.urlopen(
                f"http://info.celestial/path/gst/{gst.name}/{s.group}/{s.id}"
            ).read()

            path_data = json.loads(path_data)

            if "blocked" in path_data and path_data["blocked"]:
                logging.info(f"Path to {s} is blocked!")
                return None

            # logging.info(
            # f"Got path data for {s} to {gst.name} in {time.perf_counter() - t1}"
            # )

            return int(path_data.get("delay_us"))

        distances: typing.Dict[Sat, typing.Dict[Groundstation, float]] = {}

        t1 = time.perf_counter()

        with concurrent_futures.ThreadPoolExecutor(max_workers=128) as executor:
            futures = []

            active_sats = urllib.request.urlopen("http://info.celestial/shell/1").read()

            active_sats = json.loads(active_sats)

            for gst in self.groundstations:
                sats = [
                    Sat(sat["identifier"]["shell"], sat["identifier"]["id"])
                    for sat in active_sats["sats"]
                    if sat["active"]
                ]

                for s in sats:
                    futures.append(
                        (
                            gst,
                            s,
                            executor.submit(get_distance, gst, s),
                        )
                    )

            for f in futures:
                gst, s, distance_f = f
                distance = distance_f.result()

                if distance is None:
                    continue

                if s not in distances:
                    distances[s] = {}

                if gst in distances[s]:
                    continue

                distances[s][gst] = distance

        # now get the RMSE for each sat
        min_rmse = None
        min_sat = None
        curr_rmse = float("inf")

        for s, gst_distances in distances.items():
            if len(gst_distances) != len(self.groundstations):
                # not all groundstations have a path to this sat
                # should not happen
                logging.error(f"Not all groundstations have a path to {s}")
                continue

            rmse = 0.0
            for _, s_distance in gst_distances.items():
                if distance is None:
                    continue
                rmse += s_distance**2

            rmse = math.sqrt(rmse / len(self.groundstations))

            if s == self.deployed_sat:
                curr_rmse = rmse
                for gst, s_distance in gst_distances.items():
                    logging.info(f"curr_sat_distance: {s},{gst},{s_distance}")

            if min_rmse is None or rmse < min_rmse:
                min_rmse = rmse
                min_sat = s

        logging.info(
            f"evaluating {min_sat} (score {min_rmse}) vs {self.deployed_sat} (score {curr_rmse})"
        )

        # if the current sat is the best, do nothing
        if min_sat == self.deployed_sat:
            logging.info(f"Current sat {self.deployed_sat} is the best")
            return

        if min_rmse is None or min_sat is None:
            logging.error("No sats have a path to all groundstations")
            return

        # only do something if the new RMSE is 10+% better
        if not min_rmse < curr_rmse * 0.9:
            logging.info(
                f"New sat {min_sat} is not 10% better than current {self.deployed_sat} (curr {curr_rmse} vs new {min_rmse})"
            )
            return

        logging.info(f"Got closest sat in {time.perf_counter() - t1}")

        logging.info(
            f"currently deployed sat: {self.deployed_sat}, now deploying {min_sat}"
        )

        logging.info(f"deploy_start_info: {min_sat}")
        self.deploy_sat(min_sat)
        logging.info(f"deploy_complete_info: {min_sat}")

        # update all the clients
        for i, gst in enumerate(self.groundstations):
            logging.info(
                f"Updating client {gst.name} with sat {min_sat} (was {self.deployed_sat})"
            )
            # send the new sat to the client
            gst.update_queue.put(min_sat)

        logging.info(
            f"currently deployed sats: {[min_sat, self.deployed_sat]}, now removing {self.deployed_sat}"
        )

        # remove the old sats
        if self.deployed_sat is not None:
            logging.info(f"undeploy_start_info: {self.deployed_sat}")
            self.remove_sat(self.deployed_sat)
            logging.info(f"undeploy_complete_info: {self.deployed_sat}")

        self.deployed_sat = min_sat

        logging.info(f"currently deployed sats after removal: {self.deployed_sat}")
        logging.info(f"Updated sats in {time.perf_counter() - t1}")

    def deploy_sat(self, sat: Sat) -> None:
        deploy_functions(sat, self.deployed_sat)

    def remove_sat(self, sat: Sat) -> None:
        remove_function(sat)


constellation = Constellation()


def handler(websocket) -> None:  # type: ignore
    name = str(websocket.recv())

    logging.info(f"Got new groundstation: {name}")

    q = constellation.add_groundstation(name)

    while True:
        new_sat = q.get()
        logging.info(f"Sending new sat to {name}: {new_sat}")
        logging.info(f"switch_event: {name},{new_sat}")
        _ = websocket.send(f"{new_sat.hostname()}:8000/{ENDPOINT}")


def update_constellation() -> None:
    while True:
        constellation.update_sats()
        logging.info(
            f"Current stats: {psutil.cpu_percent()}% CPU, {psutil.virtual_memory().percent}% memory"
        )


if __name__ == "__main__":
    # listen for client positions
    # run local model
    # continuously update the satellite deployments

    if len(sys.argv) != 2:
        print("Usage: orchestrator.py <port>")
        sys.exit(1)

    logging.info(f"Starting orchestrator on port {sys.argv[1]}")

    try:
        port = int(sys.argv[1])
    except ValueError:
        print(f"Port must be an integer! Got: {sys.argv[1]}")
        sys.exit(1)

    # run the updates in the background
    threading.Thread(target=update_constellation).start()

    with websockets.sync.server.serve(handler, "0.0.0.0", port) as server:
        server.serve_forever()
