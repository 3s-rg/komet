#!/usr/bin/env python

import base64
import concurrent.futures as concurrent_futures
import logging
import sys
import typing
import queue
import threading
import time
import socket
from dataclasses import dataclass
import urllib.request
import json

import websockets.sync.server  # type: ignore
import grpc  # type: ignore
import psutil

import client_pb2 as client_pb2  # type: ignore
import client_pb2_grpc as client_pb2_grpc  # type: ignore

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s:%(levelname)s:%(filename)s: %(message)s"
)

PUT_FN = "put"
GET_FN = "get"

NUM_GROUNDSTATIONS = 1

KEYGROUP = "simple"

with open("get_fn.zip", "rb") as fi:
    f1data = fi.read()
encodedf1 = base64.b64encode(f1data).decode("utf-8")

with open("put_fn.zip", "rb") as fi:
    f2data = fi.read()
encodedf2 = base64.b64encode(f2data).decode("utf-8")


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


def deploy_functions(sats: typing.List[Sat], deployed_sats: typing.Set[Sat]) -> None:
    if len(sats) == 0:
        logging.error("No sats to deploy functions to!")
        return

    t1 = time.perf_counter()

    # wait for the sat to be available
    # sometimes this takes a bit of time at the beginning of an experiment
    # while ! nc -z localhost 9001
    for sat in sats:
        while True:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as so:
                try:
                    so.connect((sat.hostname(), 9001))
                    break
                except Exception:
                    logging.debug(f"Waiting for {sat} to be available")
                    time.sleep(0.5)

    t2 = time.perf_counter()
    logging.info(f"Sats are available in {t2 - t1}")
    fred_available_time = t2 - t1

    # if there is no sat yet, we have to create the keygroup
    if len(deployed_sats) == 0:
        sat = sats[0]
        # create keygroup
        logging.info(f"Creating keygroups for {sat}")
        r = client_pb2.CreateKeygroupRequest()  # type: ignore

        r.keygroup = KEYGROUP
        r.mutable = True
        r.expiry = 0

        stub = get_channel(f"{sat.hostname()}:9001")
        stub.CreateKeygroup(r)

        deployed_sats.add(sat)

        ur = client_pb2.UpdateRequest()  # type: ignore
        ur.keygroup = KEYGROUP
        ur.id = "0"
        ur.data = "0"

        stub.Update(ur)

    closest_sat = {}
    closest_distance = {}

    if len(deployed_sats) == 1:
        for sat in sats:
            closest_sat[sat] = list(deployed_sats)[0]
            closest_distance[sat] = 0

    else:

        def get_distance(a: Sat, b: Sat) -> typing.Optional[int]:
            # get the distance
            try:
                path_data = urllib.request.urlopen(
                    f"http://info.celestial/path/{a.group}/{a.id}/{b.group}/{b.id}"
                ).read()

                path_data = json.loads(path_data)

            except Exception as e:
                logging.error(f"Failed to get path data: {e}")
                return None

            if "blocked" in path_data and path_data["blocked"]:
                logging.info(f"Path from {sat} to {s} is blocked!")
                return None

            # logging.info(f"Got path data for {sat} to {s}: {path_data}")

            return int(path_data["delay_us"])

        logging.info(f"Getting closest sats for {sats} from {deployed_sats}")

        with concurrent_futures.ThreadPoolExecutor(max_workers=128) as executor:
            futures = []

            for sat in sats:
                if sat in deployed_sats:
                    continue
                for s in deployed_sats:
                    logging.debug(f"Getting distance from {s} to {sat}")
                    futures.append((sat, s, executor.submit(get_distance, sat, s)))

            for i, f in enumerate(futures):
                sat, s, path_data_f = f
                path_data = path_data_f.result()

                if path_data is None:
                    continue

                if sat not in closest_distance or path_data < closest_distance[sat]:
                    closest_distance[sat] = path_data
                    closest_sat[sat] = s

    if len(closest_sat.keys()) != len(sats):
        logging.error(
            f"Did not get closest sats for: {set(sats).difference(closest_sat.keys())}"
        )

    t3 = time.perf_counter()
    logging.info(f"Got closest sats in {t3 - t2}")
    closest_sat_time = t3 - t2

    with concurrent_futures.ThreadPoolExecutor(max_workers=128) as executor:
        replica_futures = []

        for sat in sats:
            if sat in deployed_sats:
                continue

            try:
                # t3 = time.perf_counter()
                # if closest_sat is None, we are the first sat
                logging.info(f"Replicating data from {closest_sat[sat]} to {sat}")
                # replicate the data from the closest sat
                r = client_pb2.AddReplicaRequest()  # type: ignore

                r.keygroup = KEYGROUP
                r.nodeId = sat.fred()

                stub = get_channel(f"{closest_sat[sat].hostname()}:9001")

                replica_futures.append((sat, executor.submit(stub.AddReplica, r)))

                # t4 = time.perf_counter()
                # logging.info(f"Replicated data to {sat} in {t4 - t3}")
            except Exception as e:
                logging.error(f"Failed to replicate data to {sat}: {e}")

                try:
                    path_data = urllib.request.urlopen(
                        f"http://info.celestial/path/{closest_sat[sat].group}/{closest_sat[sat].id}"
                    ).read()

                    path_data = json.loads(path_data)

                except Exception as e:
                    logging.error(f"Failed to get path data: {e}")
                    continue

                logging.info(f"Path data: {path_data}")

        for sat, rf in replica_futures:
            try:
                rf.result()
            except Exception as e:
                logging.error(f"Failed to replicate data {sat}: {e}")

    t4 = time.perf_counter()
    logging.info(f"Replicated data in {t4 - t3}")
    replication_time = t4 - t3

    for sat in sats:
        while True:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as so:
                try:
                    so.connect((sat.hostname(), 8080))
                    break
                except (ConnectionRefusedError, socket.timeout):
                    logging.debug(f"Waiting for {sat} to be available")
                    time.sleep(0.5)

    t5 = time.perf_counter()
    logging.info(f"Sats are available in {t5 - t4}")

    def _deploy_tf(sat: Sat, name: str, fndata: str) -> None:
        logging.info(f"Starting functions on {sat}")

        try:
            r = urllib.request.urlopen(
                f"http://{sat.hostname()}:8080/upload",
                data=json.dumps(
                    {
                        "name": name,
                        "zip": fndata,
                        "threads": 8,
                        "env": "python3",
                        "envs": [f"SATID={str(sat)}"],
                    }
                ).encode("utf-8"),
            )

            if r.status != 200:
                logging.error(f"Failed to start function: {r.read()}")

        except Exception as e:
            logging.error(f"Failed to start function: {e}")

        return

    with concurrent_futures.ThreadPoolExecutor(max_workers=128) as executor:
        deploy_futures = []

        for sat in sats:
            # send it to the middleware
            deploy_futures.append(executor.submit(_deploy_tf, sat, GET_FN, encodedf1))
            deploy_futures.append(executor.submit(_deploy_tf, sat, PUT_FN, encodedf2))

        for df in deploy_futures:
            df.result()

    t6 = time.perf_counter()
    logging.info(f"Deployed functions in {t6 - t5}")
    func_deploy_time = t6 - t5

    logging.info(f"Deployed functions in {t6 - t1}")
    logging.info(
        f"fred_available_time,closest_sat_time,replication_time,func_deploy_time = {fred_available_time},{closest_sat_time},{replication_time},{func_deploy_time}"
    )


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

    thread1 = threading.Thread(target=_delete_function, args=(GET_FN,))
    thread2 = threading.Thread(target=_delete_function, args=(PUT_FN,))

    thread1.start()
    thread2.start()

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
    thread2.join()

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

    thread1 = threading.Thread(target=_remove_keygroup, args=(KEYGROUP,))

    thread1.start()

    thread1.join()

    t3 = time.perf_counter()
    logging.info(f"Removed keygroups from {sat} in {t3 - t2}")


@dataclass
class Groundstation:
    name: str
    update_queue: queue.SimpleQueue[Sat]
    current_sat: typing.Optional[Sat]


class Constellation:
    def __init__(self) -> None:
        self.sats_deployed: typing.Dict[Sat, float] = dict()
        self.groundstations: typing.List[Groundstation] = []
        self.lock = threading.Lock()
        self.num_groundstation = NUM_GROUNDSTATIONS

    def add_groundstation(self, id: str) -> queue.SimpleQueue[Sat]:
        with self.lock:
            return self._add_groundstation(id)

    def _add_groundstation(self, id: str) -> queue.SimpleQueue[Sat]:
        update_queue = queue.SimpleQueue()  # type: ignore
        self.groundstations.append(Groundstation(id, update_queue, None))
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

        chosen_sats: typing.List[typing.Tuple[Sat, str]] = []
        closest_sat: typing.Dict[str, typing.Tuple[Sat, int]] = {}
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

                if gst.name not in closest_sat or distance < closest_sat[gst.name][1]:
                    closest_sat[gst.name] = (s, distance)

        for gst_name, data in closest_sat.items():
            logging.info(f"sat_info: {gst_name},{data[0]},{data[1]}")
            if closest_sat is not None:
                chosen_sats.append((data[0], gst_name))
            else:
                logging.error(f"No path to {gst_name}")

        logging.info(f"Got closest sats in {time.perf_counter() - t1}")

        # now we know what needs to go where
        # go through all the sats and check if they are already deployed
        # if not, deploy them
        t1 = time.perf_counter()
        new_sats: typing.Set[Sat] = set()
        for sat_info in chosen_sats:
            new_sats.add(sat_info[0])

        # if a sat has been deployed for 60+ seconds, deploy the next one
        # assuming 22 sats and ~260 seconds per handoff, with 20s to deploy
        for sat, t in self.sats_deployed.items():
            if time.time() - t > 250 or (sat.id == 2 and time.time() - t > 150):
                next_sat = sat.id - 1
                if next_sat < 0:
                    next_sat = 21
                logging.info(
                    f"Sat {sat} has been deployed for too long, also deploying {next_sat}"
                )
                new_sats.add(Sat(sat.group, next_sat))

        to_deploy = []
        for sat in new_sats:
            if sat not in self.sats_deployed.keys():
                # deploy the sat
                logging.info(f"Deploying sat {sat}")
                to_deploy.append(sat)

            else:
                logging.info(f"Sat {sat} already deployed")

        logging.info(
            f"currently deployed sats: {self.sats_deployed.keys()}, now deploying {to_deploy}"
        )

        for sat in to_deploy:
            logging.info(f"deploy_start_info: {sat}")
        self.deploy_sats(to_deploy)
        for sat in to_deploy:
            logging.info(f"deploy_complete_info: {sat}")

        # update all the clients
        for sat_info in chosen_sats:
            for i, gst in enumerate(self.groundstations):
                if gst.name == sat_info[1]:
                    # print(sat_info)
                    # print(gst.current_sat)
                    if gst.current_sat is None or gst.current_sat != sat_info[0]:
                        logging.info(
                            f"Updating client {gst.name} with sat {sat_info[0]} (was {gst.current_sat})"
                        )
                        # send the new sat to the client
                        self.groundstations[i].current_sat = sat_info[0]
                        gst.update_queue.put(sat_info[0])
                    break

        logging.info(
            f"currently deployed sats: {self.sats_deployed.keys()}, now removing {set(set(self.sats_deployed.keys())).difference(new_sats)}"
        )

        # remove the old sats
        remove_sats = set(self.sats_deployed).difference(new_sats)
        for sat in remove_sats:
            logging.info(f"undeploy_start_info: {sat}")
        self.remove_sats(remove_sats)
        for sat in remove_sats:
            logging.info(f"undeploy_complete_info: {sat}")

        logging.info(
            f"currently deployed sats after removal: {self.sats_deployed.keys()}"
        )
        logging.info(f"Updated sats in {time.perf_counter() - t1}")

    def deploy_sats(self, sats: typing.Set[Sat]) -> None:
        deploy_functions(sats, set(self.sats_deployed.keys()))
        for sat in sats:
            self.sats_deployed[sat] = time.time()

    def remove_sats(self, sats: typing.Set[Sat]) -> None:
        for sat in sats:
            del self.sats_deployed[sat]

        # do this in background
        # actually, don't do this in the background
        # it turns out a sat may be removed and then added again
        # this leads to race conditions
        with concurrent_futures.ThreadPoolExecutor(max_workers=128) as executor:
            f = []

            for sat in sats:
                f.append(executor.submit(remove_function, sat))

            for ff in f:
                ff.result()


constellation = Constellation()

sats = queue.SimpleQueue()  # type: ignore


def handler(websocket) -> None:  # type: ignore
    name = str(websocket.recv())

    logging.info(f"Got new groundstation: {name}")

    q = constellation.add_groundstation(name)

    while True:
        new_sat = q.get()
        logging.info(f"Sending new sat to {name}: {new_sat}")
        logging.info(f"switch_event: {name},{new_sat}")
        _ = websocket.send(f"{new_sat.hostname()}:8000")
        sats.put(new_sat)


def update_constellation() -> None:
    while True:
        constellation.update_sats()
        logging.info(
            f"Current stats: {psutil.cpu_percent()}% CPU, {psutil.virtual_memory().percent}% memory"
        )


def watch_keygroup():
    # in the background, we just want to know how many items are in the keygroup
    s = sats.get()
    while True:
        kr = client_pb2.KeysRequest()  # type: ignore
        kr.keygroup = KEYGROUP
        kr.id = "0"
        kr.count = 10_000

        try:
            stub = get_channel(f"{s.hostname()}:9001")
            keys = stub.Keys(kr)
            logging.info(f"keys_info: {len(keys.keys)}")
        except Exception as e:
            logging.error(f"Failed to get keys: {e}")

        try:
            new_sat = sats.get_nowait()
            s = new_sat
        except queue.Empty:
            pass

        time.sleep(1)


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

    threading.Thread(target=watch_keygroup).start()

    with websockets.sync.server.serve(handler, "0.0.0.0", port) as server:
        server.serve_forever()
