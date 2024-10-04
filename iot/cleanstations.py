#!/usr/bin/env python3

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

input_file = "stations-full.csv"
output_file = "stations.toml"

# focus on the pacific
min_lat_1 = 25
max_lat_1 = 90
min_lon_1 = -180
max_lon_1 = -100

min_lat_2 = 25
max_lat_2 = 90
min_lon_2 = 140
max_lon_2 = 180

if __name__ == "__main__":
    stations = []
    with open(input_file, "r") as f:
        with open(output_file, "w") as out:
            lines = f.readlines()

            for line in lines:
                if "dart" not in line.lower():
                    continue

                parts = line.split("|")
                station_id = parts[0].strip()

                location_raw = parts[6].strip()
                location_parts = location_raw.split(" ")

                lat = float(location_parts[0].strip()) * (
                    -1 if location_parts[1] == "S" else 1
                )
                lon = float(location_parts[2].strip()) * (
                    -1 if location_parts[3] == "W" else 1
                )

                stations.append((station_id, lat, lon))

                if (
                    lat < min_lat_1
                    or lat > max_lat_1
                    or lon < min_lon_1
                    or lon > max_lon_1
                ) and (
                    lat < min_lat_2
                    or lat > max_lat_2
                    or lon < min_lon_2
                    or lon > max_lon_2
                ):
                    print(f"Skipping {station_id} at {lat}, {lon}")
                    continue

                out.write(f"""
# {line.strip()}
[[ground_station]]
name = "sensor{station_id}"
lat = {lat}
long = {lon}
""")

    df = pd.DataFrame(stations, columns=["station_id", "lat", "lon"])
    sns.scatterplot(x="lon", y="lat", data=df)
    sns.despine()
    # add red square for the region we like
    plt.plot(
        [min_lon_1, max_lon_1, max_lon_1, min_lon_1, min_lon_1],
        [min_lat_1, min_lat_1, max_lat_1, max_lat_1, min_lat_1],
        "r-",
    )
    plt.plot(
        [min_lon_2, max_lon_2, max_lon_2, min_lon_2, min_lon_2],
        [min_lat_2, min_lat_2, max_lat_2, max_lat_2, min_lat_2],
        "r-",
    )
    plt.savefig("stations.png")
