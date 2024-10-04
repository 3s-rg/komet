#!/usr/bin/env python3

import logging
import os
import random
import sys
import threading
import time
import typing

import redis
import requests
import websockets.sync.client as ws_client

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s:%(levelname)s:%(filename)s: %(message)s"
)


class RedisClient:
    def __init__(self):
        self.client = None
        self._lock = threading.Lock()

    def connect(self, host: str, port: int) -> None:
        if self.client is not None:
            self.disconnect()
        self.client = redis.Redis(host=host, port=port, db=0)
        # try to connect
        self.client.ping()

    def disconnect(self) -> None:
        self.client.close()

    def lock(self) -> None:
        self._lock.acquire()

    def unlock(self) -> None:
        self._lock.release()

    def get(self, key: str) -> str:
        while self.client is None:
            pass

        self.lock()
        value = self.client.get(key)
        self.unlock()
        return value

    def set(self, key: str, value: str) -> None:
        while self.client is None:
            pass

        self.lock()
        self.client.set(key, value)
        self.unlock()

    def fill(self, keys: typing.List[str], bytes_per_key: int = 1_048_576):
        while self.client is None:
            pass

        self.lock()

        logging.info("Disabling persistence")
        self.client.config_set("save", "")
        self.client.config_set("appendonly", "no")

        logging.info("Filling redis")
        pipe = self.client.pipeline()

        t0 = time.perf_counter()
        t1 = time.perf_counter()
        for key in keys:
            # random data is better, doesn't compress as well
            # pipe.set(key, "a" * bytes_per_key)
            pipe.set(key, os.urandom(bytes_per_key))
            # 100 keys at a time is good, takes about 1 second
            if len(pipe.command_stack) == 100:
                pipe.execute()
                logging.info(f"Filled 100 keys in {time.perf_counter() - t1} seconds")
                t1 = time.perf_counter()
        t2 = time.perf_counter()
        pipe.execute()
        logging.info(f"Filled remaining keys in {t2 - t1} seconds")

        logging.info(f"Filled redis in {time.perf_counter() - t0} seconds")

        self.unlock()


def control_migration(r: RedisClient, komet_host: str) -> None:
    # setup connection to komet
    with ws_client.connect(f"ws://{komet_host}") as ws:
        # get the initial selected sat
        sat = str(ws.recv())
        logging.info(f"Initial selected sat: {sat}")

        # start the server
        while True:
            try:
                response = requests.post(f"http://{sat}/start_container")
                if response.status_code != 200:
                    print(f"Failed to start container: {response.text}")
                    exit(1)
                logging.info("Started container")
                break
            except Exception:
                logging.info("Failed to connect to sat, retrying")
                time.sleep(1)

        r.connect(sat, 6379)
        r.unlock()

        while True:
            # get new best server and migrate
            new_sat = str(ws.recv())

            logging.info(f"New selected sat: {new_sat}")

            r.lock()
            t1 = time.perf_counter()
            # instruct the new sat to start the container
            logging.info(f"Starting migration to {new_sat}")
            r.disconnect()

            response = requests.post(
                f"http://{new_sat}/do_migration",
                json={"source": sat},
            )
            if response.status_code != 200:
                print(f"Failed to migrate container: {response.text}")
                exit(1)

            logging.info(f"Migration to {new_sat} successful")

            # read the response
            info = response.json()
            logging.info(f"Migration info: {info}")

            logging.info(f"Setting up connection to {new_sat}")

            while True:
                try:
                    r.connect(new_sat, 6379)
                    logging.info("Connected to redis")
                    break
                except Exception:
                    logging.info("Failed to connect to redis, retrying")
                    time.sleep(1)

            sat = new_sat
            t2 = time.perf_counter()
            r.unlock()

            logging.info(f"Migration took {t2 - t1} seconds")


if __name__ == "__main__":
    # get the komet host from args
    if len(sys.argv) != 3:
        print("Usage: client.py <komet_host> <N>")
        sys.exit(1)

    komet_host = sys.argv[1]
    N = int(sys.argv[2])

    # make N random but distinct keys and insert them into the redis
    known_keys = [f"k{i}" for i in range(N)]

    # instruct the sat to start the container
    r = RedisClient()
    r.lock()

    # start the control thread
    t = threading.Thread(target=control_migration, args=(r, komet_host))
    t.start()

    # fill the redis
    r.fill(known_keys, bytes_per_key=1_048_576)

    # add a single small key to make sure we have something
    r.set("small", "a")
    known_keys.append("small")

    while True:
        # get a random key
        key = random.choice(known_keys)
        logging.info(f"Getting key {key}")

        # make sure the key is still there
        value = r.get(key)

        if value is None:
            print(f"Key {key} disappeared")
            exit(1)

        logging.info(f"Got key {key}")

        time.sleep(1)
