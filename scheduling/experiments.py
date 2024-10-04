#!/usr/bin/env python3

import strategies

from dataclasses import dataclass


@dataclass
class Experiment:
    name: str
    zip_file: str
    client_prefix: str
    duration: int
    resolution: int
    strategy: strategies.Strategy

    def filename(self):
        return f"{self.name}-{str(self.strategy)}"


RESULTS_FOLDER = "results"

_simple_experiments = [
    Experiment(
        "simple",
        "simple-full.zip",
        "redmond",
        1200,
        1,
        strategies.OneToOneStrategy(threshold=0.1),
    ),
    Experiment(
        "simple",
        "simple-full.zip",
        "redmond",
        1200,
        1,
        strategies.OneToOneStrategy(threshold=0.25),
    ),
    Experiment(
        "simple",
        "simple-full.zip",
        "redmond",
        1200,
        1,
        strategies.OneToOneAbsoluteStrategy(absolute_threshold=500),
    ),
    Experiment(
        "simple",
        "simple-full.zip",
        "redmond",
        1200,
        1,
        strategies.MinMaxStrategy(to_select="one"),
    ),
]

_iot_experiments = [
    Experiment(
        "iot",
        "iot-full.zip",
        "sensor",
        1200,
        1,
        strategies.ManyToOneStrategy(agg="rmse", threshold=0.1),
    ),
    Experiment(
        "iot",
        "iot-full.zip",
        "sensor",
        1200,
        1,
        strategies.ManyToOneStrategy(agg="rmse", threshold=0.25),
    ),
    Experiment(
        "iot",
        "iot-full.zip",
        "sensor",
        1200,
        1,
        strategies.StickyStrategy(trajectory_file="iot-full.zip"),
    ),
    Experiment(
        "iot",
        "iot-full.zip",
        "sensor",
        1200,
        1,
        strategies.MinMaxStrategy(to_select="one"),
    ),
]

_cdn_experiments = [
    Experiment(
        "cdn",
        "cdn-full.zip",
        "client",
        1200,
        1,
        strategies.ManyToManyStrategy(threshold=0.1),
    ),
    Experiment(
        "cdn",
        "cdn-full.zip",
        "client",
        1200,
        1,
        strategies.ManyToManyStrategy(threshold=0.25),
    ),
    Experiment(
        "cdn",
        "cdn-full.zip",
        "client",
        1200,
        1,
        strategies.ManyToManyAbsoluteStrategy(absolute_threshold=1000),
    ),
    Experiment(
        "cdn",
        "cdn-full.zip",
        "client",
        1200,
        1,
        strategies.MinMaxStrategy(to_select="many"),
    ),
    Experiment(
        "cdn",
        "cdn-full.zip",
        "client",
        1200,
        1,
        strategies.ManyToManyFixedStrategy(max_sats=3, threshold=0.1),
    ),
    Experiment(
        "cdn",
        "cdn-full.zip",
        "client",
        1200,
        1,
        strategies.ManyToManyFixedStrategy(max_sats=5, threshold=0.1),
    ),
]


_iotgraph_experiments = [
    Experiment(
        "iotgraph",
        "iot-full.zip",
        "sensor",
        1200,
        1,
        strategies.ManyToOneStrategy(
            threshold=x / 100,
            agg="rmse",
        ),
    )
    for x in range(0, 51, 5)
] + [
    Experiment(
        "iotgraph",
        "iot-full.zip",
        "sensor",
        1200,
        1,
        strategies.MinMaxStrategy(
            to_select="one",
        ),
    )
]

_iotgraphextreme_experiments = [
    Experiment(
        "iotgraphextreme",
        "iot-extreme.zip",
        "sensor",
        3600,
        1,
        strategies.ManyToOneStrategy(
            threshold=x / 100,
            agg="rmse",
        ),
    )
    for x in range(0, 51, 5)
] + [
    Experiment(
        "iotgraphextreme",
        "iot-extreme.zip",
        "sensor",
        3600,
        1,
        strategies.MinMaxStrategy(
            to_select="one",
        ),
    ),
    Experiment(
        "iotgraphextreme",
        "iot-extreme.zip",
        "sensor",
        3600,
        1,
        strategies.StickyStrategy(
            trajectory_file="iot-extreme.zip",
        ),
    ),
]

_simplegraph_experiments = [
    Experiment(
        "simplegraph",
        "simple-full.zip",
        "redmond",
        1200,
        1,
        strategies.OneToOneStrategy(
            threshold=x / 100,
        ),
    )
    for x in range(0, 51, 5)
] + [
    Experiment(
        "simplegraph",
        "simple-full.zip",
        "redmond",
        1200,
        1,
        strategies.MinMaxStrategy(
            to_select="one",
        ),
    )
]

EXPERIMENTS = (
    _iotgraphextreme_experiments
    + _iotgraph_experiments
    + _simple_experiments
    + _iot_experiments
    + _cdn_experiments
    + _simplegraph_experiments
)
