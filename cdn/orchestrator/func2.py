#!/usr/bin/env python3

# on import, set up the database connection
import subprocess
import logging
import concurrent.futures
import time
import typing

import grpc  # type: ignore

# import middleware_pb2 as middleware_pb2  # type: ignore
# import middleware_pb2_grpc as middleware_pb2_grpc  # type: ignore
import client_pb2 as client_pb2  # type: ignore
import client_pb2_grpc as client_pb2_grpc  # type: ignore


with open("cert.crt") as f:
    crt = f.read().encode()

with open("cert.key") as f:
    key = f.read().encode()

with open("ca.crt") as f:
    ca = f.read().encode()

creds = grpc.ssl_channel_credentials(ca, key, crt)

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(message)s")


def logflush() -> None:
    for handler in logging.getLogger().handlers:
        handler.flush()


# connect to the gateway
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

# stub = middleware_pb2_grpc.MiddlewareStub(
#     grpc.secure_channel(
#         f"{gateway}:10000",
#         creds,
#     )
# )
stub = client_pb2_grpc.ClientStub(
    grpc.secure_channel(
        f"{gateway}:9001",
        creds,
        options=(("grpc.ssl_target_name_override", "localhost"),),
    )
)


# thanks, ChatGPT!
def last_hundred_unique_items(lst: typing.List[str]) -> typing.Set[str]:
    seen = set()
    unique_items = set()

    for item in reversed(lst):
        if item not in seen:
            seen.add(item)
            unique_items.add(item)
        if len(unique_items) == 500:
            break

    return unique_items


def fn(_: str) -> str:
    logging.info("Running delete function")

    # go through the most recent 1000 requests
    # delete everything in the keygroup that is not part of that

    # make sure there is an anchor item in the log keygroup

    t1 = time.perf_counter()

    logging.debug("checking number of keys")

    try:
        kr = client_pb2.KeysRequest()
        kr.keygroup = "cdn"
        kr.id = "a"
        kr.count = 10_000

        num_keys = len(stub.Keys(kr).keys)
        logging.debug(f"Number of keys in cdn: {num_keys}")
    except Exception as e:
        logging.error(f"Failed to get number of keys: {e}")
        return "Failed"

    if num_keys < 1000:
        logging.debug("Not enough keys, skipping deletion")
        return "Not enough keys"

    t2 = time.perf_counter()

    logging.debug(f"Got number of keys in {t2 - t1} seconds")

    logging.debug("adding anchor to log")

    try:
        ar = client_pb2.AppendRequest()
        ar.keygroup = "log"
        ar.id = 0
        ar.data = "0"

        stub.Append(ar)
    except Exception as e:
        logging.error(f"Failed to update log with anchor: {e}")
        # assuming something else is doing deletion
        logging.debug("skipping deletion")
        # as close as we are going to get to a distributed lock
        # will expire in a few seconds anyway
        return

    logging.debug("not skipping deletion!")

    t3 = time.perf_counter()

    logging.debug(f"added anchor to log in {t3 - t2} seconds")

    logging.debug("adding anchor to cdn")
    try:
        # add a new anchor item to the cdn group
        ur = client_pb2.UpdateRequest()
        ur.keygroup = "cdn"
        ur.id = "a"
        ur.data = "a"

        stub.Update(ur)
    except Exception as e:
        logging.error(f"Failed to update cdn with anchor: {e}")
        # that's fine

    t4 = time.perf_counter()
    logging.debug(f"added anchor to cdn in {t4 - t3} seconds")

    most_recent = [(0, "0")]

    # we kind of need to read everything starting at 0
    while True:
        try:
            sr = client_pb2.ScanRequest()  # type: ignore
            sr.keygroup = "log"
            sr.id = str(most_recent[-1][0])
            sr.count = 1000

            new_items = [(data.id, data.val) for data in stub.Scan(sr).data][1:]

            logging.debug(f"Got {len(new_items)} new items from log")

            if len(new_items) == 0:
                break

            most_recent = most_recent + new_items
        except Exception as e:
            logging.error(f"Failed to scan log: {e}")
            break

    t5 = time.perf_counter()

    logging.debug(
        f"Got {len(most_recent)} items in total from log in {t5 - t4} seconds"
    )

    # to_keep = set((id for _, id in most_recent[-100:]))
    to_keep = last_hundred_unique_items(most_recent)
    to_keep.add("a")

    known_items = ["a"]

    # we kind of need to read everything starting at 0
    # but do max 10 iterations
    for i in range(10):
        try:
            kr = client_pb2.KeysRequest()  # type: ignore
            kr.keygroup = "cdn"
            kr.id = known_items[-1]
            kr.count = 1000

            new_items = [k.id for k in stub.Keys(kr).keys][1:]

            logging.debug(f"Got {len(new_items)} new items in cdn")

            if len(new_items) == 0:
                break

            known_items = known_items + new_items
            logging.debug(
                f"Got {len(known_items)} items in total in cdn after iteration {i}"
            )
        except Exception as e:
            logging.error(f"Failed to scan cdn: {e}")
            break

    t6 = time.perf_counter()

    logging.debug(f"Got {len(known_items)} items in total in cdn in {t6 - t5} seconds")

    delete_set = set(known_items) - to_keep

    logging.debug(f"Deleting {len(delete_set)} items")
    logging.debug(f"Keeping {len(to_keep)} items")
    # logging.debug(f"known items: {known_items}")
    # logging.debug(f"to keep: {to_keep}")

    def delete_item(item: str) -> None:
        try:
            dr = client_pb2.DeleteRequest()
            dr.keygroup = "cdn"
            dr.id = item

            stub.Delete(dr)
            # logging.debug(f"Deleted item {item}")
        except Exception as e:
            logging.error(f"Failed to delete item {item}: {e}")

    t7 = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=128) as executor:
        f = executor.map(delete_item, delete_set)

        concurrent.futures.wait(f)

    t8 = time.perf_counter()
    logging.info(f"Deleting took {t8 - t7} seconds")

    # logging.debug("deleting anchor")
    # try:
    #     try:
    #         dr = client_pb2.DeleteRequest()
    #         dr.keygroup = "log"
    #         dr.id = "0"

    #         stub.Delete(dr)
    #         # logging.debug(f"Deleted item {item}")
    #     except Exception as e:
    #         logging.error(f"Failed to delete anchor 0 from log: {e}")

    # except Exception as e:
    #     logging.error(f"Failed to delete anchor: {e}")

    t9 = time.perf_counter()

    logging.info(f"Total time: {t9 - t1} seconds")

    # logging.flush()
    logflush()
    return "Done"
