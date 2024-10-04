#!/usr/bin/env python3

import os
import logging
import random
import subprocess

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s:%(levelname)s:%(filename)s: %(message)s"
    )

    STAGES = list(range(0, 1000, 100)) + [1_000]

    REPEATS = 3

    experiments = [
        {
            "stage": stage,
            "repeat": i + 1,
        }
        for stage in STAGES
        for i in range(REPEATS)
    ]

    # randomize
    random.shuffle(experiments)

    for i in range(10):
        # just repeat this a bunch of times to make sure all experiments have run
        for experiment in experiments:
            output_file = f"./simple_scale/output/{experiment['stage']}_{experiment['repeat']}.out"
            # if there is already an output file, skip
            if os.path.exists(output_file):
                logging.info(f"Skipping experiment {experiment}")
                continue

            logging.info(f"Running experiment {experiment}")
            with open("./simple_scale/cfg.txt", "w") as f:
                f.write(f"{experiment['stage']}\n")
            # ./experiment.sh 10.35.6.3 containers
            p = subprocess.run(
                ["./experiment.sh", "10.35.6.4", "simple_scale"],
            )
            if p.returncode != 0:
                logging.error(f"Experiment {experiment} failed")
                continue

            # output goes into the containers/out directory
            os.makedirs("./simple_scale/output", exist_ok=True)
            # take the ./containers/gst-HKPU.out file and move it
            os.rename(
                "./simple_scale/out/gst-orchestrator.out",
                output_file,
            )

    logging.info("All experiments completed")
