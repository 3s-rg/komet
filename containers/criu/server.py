#!/usr/bin/env python3
import logging
import os
import subprocess
import time

import requests
import flask


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s:%(levelname)s:%(filename)s: %(message)s"
)

# checkpoint_dir = "/tmp"
checkpoint_dir = "/mnt/criu"

app = flask.Flask(__name__)


@app.route("/start_container", methods=["POST"])
def start_container():
    # podman run -d --name cr-container redis:latest
    logging.info("Starting container")
    p = subprocess.run(
        [
            "podman",
            "run",
            "-d",
            "-p",
            "6379:6379",
            "--name",
            "cr-container",
            "redis:alpine",
        ],
        capture_output=True,
    )

    if p.returncode != 0:
        logging.error("Failed to start container: %s", p.stderr)
        return flask.Response(status=500, response="Failed to start container")

    # print some logs
    p = subprocess.run(
        ["podman", "logs", "cr-container"],
        capture_output=True,
    )

    if p.returncode != 0:
        logging.error("Failed to get logs: %s", p.stderr)
        return

    logging.info("Container started")
    logging.info("Logs:")
    logging.info(p.stdout.decode("utf-8"))

    return flask.Response(status=200, response="Container started")


@app.route("/do_migration", methods=["POST"])
def migrate():
    # parse the JSON input to find out "from"
    source = flask.request.json["source"]

    logging.info(f"Doing migration from {source}")

    t1 = time.perf_counter()

    # get the checkpoint
    r = requests.get(f"http://{source}/give_checkpoint", stream=True)

    t2 = time.perf_counter()

    if r.status_code != 200:
        logging.error("Failed to get checkpoint: %s", r.status_code)
        return flask.Response(status=500, response="Failed to get checkpoint")

    logging.info("Got checkpoint")
    logging.info(f"Getting checkpoint took {t2 - t1} seconds")

    other_checkpoint_size = int(r.headers["X-Checkpoint-Size"])
    other_checkpoint_time = float(r.headers["X-Checkpoint-Time"])

    # write the checkpoint to a file
    checkpoint_path = os.path.join(checkpoint_dir, "checkpoint.tar")

    with open(checkpoint_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)

    t3 = time.perf_counter()

    logging.info(f"Received checkpoint at {checkpoint_path}")
    logging.info(f"Receiving took {t3 - t2} seconds")
    checkpoint_size = os.path.getsize(checkpoint_path)
    logging.info(
        f"Checkpoint size: {checkpoint_size} bytes, {checkpoint_size / 1024 / 1024} MB"
    )

    p = subprocess.run(
        [
            "podman",
            "container",
            "restore",
            # "--tcp-established",
            "--ignore-rootfs",
            f"--import={checkpoint_path}",
        ],
        capture_output=True,
    )

    t4 = time.perf_counter()

    if p.returncode != 0:
        logging.error("Failed to restore container: %s", p.stderr)

        # get the log file
        # error looks like:
        # Error: OCI runtime error: runc: criu failed: type NOTIFY errno 0\nlog file: /var/lib/containers/storage/overlay-containers/15c66433818e816f7da6ecb04544e63a59c8ea28ebd1a8ef356be842f1249ce9/userdata/restore.log\n
        log_file = (
            p.stderr.decode("utf-8").split("log file: ")[1].split('"\n')[0].strip()
        )

        with open(log_file, "r") as f:
            logging.error(f.read())

        return flask.Response(status=500, response="Failed to restore container")

    logging.info("Restored container")
    logging.info(f"Restore took {t4 - t3} seconds")

    # print podman ps
    p = subprocess.run(["podman", "ps"], capture_output=True)

    if p.returncode != 0:
        logging.error("Failed to get podman ps: %s", p.stderr)
        return

    logging.info("Podman ps:")
    logging.info(p.stdout.decode("utf-8"))

    # print podman logs
    p = subprocess.run(["podman", "logs", "cr-container"], capture_output=True)

    if p.returncode != 0:
        logging.error("Failed to get podman logs: %s", p.stderr)
        return

    logging.info("Podman logs cr-container:")
    logging.info(p.stdout.decode("utf-8"))

    return flask.jsonify(
        {
            "receive_time": t2 - t1,
            "restore_size": checkpoint_size,
            "restore_time": t4 - t3,
            "total_time": t4 - t1,
            "other_checkpoint_size": other_checkpoint_size,
            "other_checkpoint_time": other_checkpoint_time,
        },
    )


@app.route("/give_checkpoint", methods=["GET"])
def give_checkpoint():
    logging.info("Starting migration")

    logging.info("Accepted migration request")

    t1 = time.perf_counter()

    checkpoint_path = os.path.join(checkpoint_dir, "checkpoint.tar")

    p = subprocess.run(
        [
            "podman",
            "container",
            "checkpoint",
            "cr-container",
            # "--tcp-established",
            "--ignore-rootfs",
            f"-e={checkpoint_path}",
        ],
        capture_output=True,
    )

    if p.returncode != 0:
        logging.error("Failed to checkpoint container: %s", p.stderr)

        # get the log file
        # error looks like:
        # ERROR:root:Failed to checkpoint container: b'time="2024-04-09T10:00:55Z" level=error msg="container still running"\ntime="2024-04-09T10:00:55Z" level=error msg="criu failed: type NOTIFY errno 0\\nlog file: /var/lib/containers/storage/overlay-containers/23646ff35431398c527238932129d1b56bbc12528fed89db5a4d2019938fbb55/userdata/dump.log"\nError: `/usr/bin/runc checkpoint --image-path /var/lib/containers/storage/overlay-containers/23646ff35431398c527238932129d1b56bbc12528fed89db5a4d2019938fbb55/userdata/checkpoint --work-path /var/lib/containers/storage/overlay-containers/23646ff35431398c527238932129d1b56bbc12528fed89db5a4d2019938fbb55/userdata 23646ff35431398c527238932129d1b56bbc12528fed89db5a4d2019938fbb55` failed: exit status 1\n'
        log_file = (
            p.stderr.decode("utf-8").split("log file: ")[1].split('"\n')[0].strip()
        )

        with open(log_file, "r") as f:
            logging.error(f.read())

        return flask.Response(status=500, response="Failed to checkpoint container")

    t2 = time.perf_counter()
    logging.info("Checkpointed container")
    logging.info(f"Checkpoint took {t2 - t1} seconds")
    checkpoint_size = os.path.getsize(checkpoint_path)
    logging.info(
        f"Checkpoint size: {checkpoint_size} bytes, {checkpoint_size / 1024 / 1024} MB"
    )
    logging.info("Sending checkpoint to target")

    t3 = time.perf_counter()

    r = flask.make_response(
        flask.send_file(checkpoint_path, mimetype="application/gzip")
    )
    r.headers["X-Checkpoint-Size"] = str(checkpoint_size)
    r.headers["X-Checkpoint-Time"] = str(t2 - t1)

    logging.info("Sent checkpoint")

    t4 = time.perf_counter()

    logging.info(f"Migration took {t4 - t3} seconds")

    # delete the container
    t5 = time.perf_counter()

    # p = subprocess.run(["podman", "rm", "cr-container"])

    # if p.returncode != 0:
    #     logging.error("Failed to remove container: %s", p.stderr)
    #     return flask.Response(status=500, response="Failed to remove container")

    t6 = time.perf_counter()

    # logging.info(f"Cleanup took {t6 - t5} seconds")
    logging.info(f"Total migration took {t6 - t1} seconds")

    return r


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
