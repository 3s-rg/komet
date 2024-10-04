#!/usr/bin/env python3

# STAGES=( "0" "1_000" "10_000" "25_000" "50_000" "100_000" "250_000" "500_000" "1_000_000" "2_500_000" "5_000_000" )

# for STAGE in "${STAGES[@]}"
# do
#     echo "Running stage $STAGE"
#     echo "$STAGE" > ./containers/cfg.txt
#     ./experiment.sh 10.35.6.3 containers
# done

import os
import logging
import random
import subprocess

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s:%(levelname)s:%(filename)s: %(message)s"
    )

    # STAGES = [
    #     0,
    #     1,
    #     5,
    #     10,
    #     25,
    #     50,
    #     100,
    #     250,
    #     500,
    #     1_000,
    # ] + list(range(0, 1000, 100))
    STAGES = list(range(0, 1000, 100)) + [1_000]

    REPEATS = 10

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
            output_file = (
                f"./containers/out/{experiment['stage']}_{experiment['repeat']}.out"
            )
            # if there is already an output file, skip
            if os.path.exists(output_file):
                logging.info(f"Skipping experiment {experiment}")
                continue

            logging.info(f"Running experiment {experiment}")
            with open("./containers/cfg.txt", "w") as f:
                f.write(f"{experiment['stage']}\n")
            # ./experiment.sh 10.35.6.3 containers
            # redirect stdout to stdout
            p = subprocess.run(
                ["./experiment.sh", "10.35.6.3", "containers"],
                # stdout=subprocess.STDOUT,
                # stderr=subprocess.STDOUT,
            )
            if p.returncode != 0:
                logging.error(f"Experiment {experiment} failed")
                continue

            # output goes into the containers/out directory
            os.makedirs("./containers/out", exist_ok=True)
            # take the ./containers/gst-HKPU.out file and move it
            os.rename(
                "./containers/gst-HKPU.out",
                output_file,
            )

    logging.info("All experiments completed")
