#!/usr/bin/env python3

import concurrent.futures
import sys
import typing
import os

import celestial.types
import celestial.zip_serializer

import tqdm

import experiments


def do_experiment(e: experiments.Experiment):
    serializer = celestial.zip_serializer.ZipDeserializer(e.zip_file)

    config = serializer.config()

    ground_stations = []
    ground_station_names = {}

    for i, g in enumerate(config.ground_stations):
        ground_station_names[i] = g.name
        if g.name.startswith(e.client_prefix):
            ground_stations.append(i)

    num_sats = config.shells[0].planes * config.shells[0].sats

    traffic_matrix: typing.List[typing.List[typing.Union[float, int]]] = [
        [float("inf") for _ in range(num_sats)] for _ in range(len(ground_stations))
    ]

    results_file = f"{os.path.join(experiments.RESULTS_FOLDER, e.filename())}.csv"

    e.strategy.init(ground_stations, num_sats)

    with open(results_file, "w") as f:
        f.write("t,ground_station,satellite,distance\n")

    for t in tqdm.trange(0, e.duration, e.resolution, desc=e.filename()):
        # first update the traffic matrix
        links = serializer.diff_links(t + config.offset)

        for link in links:
            if not celestial.types.MachineID_group(link[0]) == 0:
                # sat to sat link, do not care
                continue

            # ground station
            # skip if its not in our list
            if not ground_station_names[
                int(celestial.types.MachineID_id(link[0]))
            ].startswith(e.client_prefix):
                continue

            if celestial.types.MachineID_group(link[1]) == 0:
                # target is also a ground station
                # don't care
                continue

            # target is a satellite
            sat_id = int(celestial.types.MachineID_id(link[1]))
            g_index = int(ground_stations.index(celestial.types.MachineID_id(link[0])))

            traffic_matrix[g_index][sat_id] = (
                celestial.types.Link_latency_us(link[2])
                if not celestial.types.Link_blocked(link[2])
                else float("inf")
            )

        # then evaluate the strategy
        # what do we care about as a return type?
        # selected sats and assignments
        e.strategy.update(t, traffic_matrix)

        # then write down the stats at this moment
        with open(results_file, "a") as f:
            for assignment in e.strategy.sat_assignments():
                f.write(
                    f"{t},{ground_station_names[assignment[0]]},{assignment[1]},{traffic_matrix[int(
                    ground_stations.index(assignment[0]))
                ][int(assignment[1])]}\n"
                )

    serializer.close()


if __name__ == "__main__":
    os.makedirs(experiments.RESULTS_FOLDER, exist_ok=True)

    if len(sys.argv) > 1 and sys.argv[1] == "--debug":
        print("Running in debug mode (sequential execution)")
        for experiment in experiments.EXPERIMENTS:
            do_experiment(experiment)
    else:
        with concurrent.futures.ProcessPoolExecutor() as executor:
            executor.map(do_experiment, experiments.EXPERIMENTS)
