#!/usr/bin/env python3

from dataclasses import dataclass
import logging
import sys
import time
import threading
import typing

import requests
import websockets.sync.server

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s:%(levelname)s:%(filename)s: %(message)s"
)

# logging.basicConfig(
#     level=logging.DEBUG, format="%(asctime)s:%(levelname)s:%(filename)s: %(message)s"
# )


@dataclass
class Sat:
    group: int
    id: int
    distance: float

    def hostname(self) -> str:
        return f"{self.id}.{self.group}.celestial"

    def __str__(self) -> str:
        return self.hostname()

    def __repr__(self) -> str:
        return f"Sat(group={self.group}, id={self.id}, distance={self.distance})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Sat):
            return False

        return self.group == other.group and self.id == other.id


class Constellation:
    def __init__(self):
        # get the sats
        # assume shell = 1 for now
        # TODO: get the number of shells and figure out migration
        self.num_shells = 1

        # get the name
        self.name = requests.get("http://info.celestial/self").json()["identifier"][
            "name"
        ]

        logging.info(f"Got name: {self.name}")

        self.lock = threading.Lock()
        self.update_sats()

    def update_sats(self) -> None:
        sats = []

        for sat in requests.get("http://info.celestial/shell/1").json()["sats"]:
            # get the distance
            path_data = requests.get(
                f"http://info.celestial/path/gst/{self.name}/{sat['identifier']['shell']}/{sat['identifier']['id']}"
            ).json()

            if "blocked" in path_data and path_data["blocked"]:
                logging.debug(f"Path to {sat['identifier']} is blocked!")
                continue

            try:
                logging.debug(f"Got path data for {sat['identifier']}: {path_data}")
                sats.append(
                    Sat(
                        group=sat["identifier"]["shell"],
                        id=sat["identifier"]["id"],
                        distance=path_data["delay_us"],
                    )
                )
            except KeyError:
                logging.error(
                    f"Could not get path data for {sat['identifier']}: {path_data}"
                )

        with self.lock:
            self.sats = sats

    def get_best_sat(self) -> typing.Optional[Sat]:
        self.update_sats()

        if len(self.sats) == 0:
            logging.warning("No sats available!")
            return None

        with self.lock:
            min_sat = min(self.sats, key=lambda x: x.distance)
            if time.time_ns() % 10 == 0:
                # little hack to make the logs less spammy
                logging.info(f"Best sat: {min_sat}")
            return min_sat


def handler(websocket):
    # gets the best server and returns it

    # init a constellation
    constellation = Constellation()

    best_server = None
    while True:
        new_best_server = constellation.get_best_sat()
        if new_best_server != best_server:
            logging.info(f"New best server: {new_best_server.hostname()}")
            best_server = new_best_server
            websocket.send(best_server.hostname())
            logging.info(f"Sent new best server: {best_server.hostname()}")

        # time.sleep(1)


if __name__ == "__main__":
    # get argument 1: the port

    if len(sys.argv) != 2:
        print("Usage: komet.py <port>")
        sys.exit(1)

    logging.info(f"Starting Komet server on port {sys.argv[1]}")

    try:
        port = int(sys.argv[1])
    except ValueError:
        print(f"Port must be an integer! Got: {sys.argv[1]}")
        sys.exit(1)

    with websockets.sync.server.serve(handler, "localhost", port) as server:
        server.serve_forever()
