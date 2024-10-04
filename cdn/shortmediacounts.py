#!/usr/bin/env python3

# small script to reduce the amount of media counts to something more manageable
# should be about 100MB

import tqdm
import re

INPUT_FILE = "mediacounts.2024-04-28.v00.tsv"

if __name__ == "__main__":
    # figure out the line count for the input file
    print(f"Counting lines in {INPUT_FILE}...")
    line_count = 0
    with open(INPUT_FILE, "r") as f:
        for line in f:
            line_count += 1
    print(f"Found {line_count} lines in {INPUT_FILE}")

    with open(INPUT_FILE, "r") as f:
        i = 0
        with open("shortmedia-full.csv", "w") as o_full:
            with open("shortmedia.csv", "w") as o_reduced:
                o_full.write("base_name,v,len,N_access\n")
                o_reduced.write("base_name,v,len,N_access\n")

                # read line by line
                for line in tqdm.tqdm(f, total=line_count):
                    # check if in /wikipedia/commons or /wikipedia/en or /wikipedia/zh
                    if (
                        not line.startswith("/wikipedia/commons")
                        and not line.startswith("/wikipedia/en")
                        and not line.startswith("/wikipedia/zh")
                    ):
                        continue

                    parts = line.split("\t")

                    basename = parts[0]

                    # check if the line is for a video
                    transcoded_movie = int(parts[16])

                    if transcoded_movie > 0:
                        continue

                    # same for audio file
                    transcoded_audio = int(parts[4])

                    if transcoded_audio > 0:
                        continue

                    # calculate the OG size of the photo
                    original = int(parts[3])
                    transcoded_image = int(parts[7])
                    transcoded_image_0_199 = int(parts[8])
                    transcoded_image_200_399 = int(parts[9])
                    transcoded_image_400_599 = int(parts[10])
                    transcoded_image_600_799 = int(parts[11])
                    transcoded_image_800_999 = int(parts[12])
                    transcoded_image_1000 = int(parts[13])

                    transcoded_rest = transcoded_image - (
                        transcoded_image_0_199
                        + transcoded_image_200_399
                        + transcoded_image_400_599
                        + transcoded_image_600_799
                        + transcoded_image_800_999
                        + transcoded_image_1000
                    )

                    total_response_size = int(parts[1])

                    # assuming the original width is 2000px, so image_1000 is 25% size, image_800_999 is 20% size, image_600_799 is 15% size, image_400_599 is 10% size, image_200_399 is 5% size, image_0_199 is 1% size
                    # now figure out the size of the original image using some cool arithmetic
                    original_size = total_response_size / (
                        0.25 * transcoded_image_1000
                        + 0.2 * transcoded_image_800_999
                        + 0.15 * transcoded_image_600_799
                        + 0.1 * transcoded_image_400_599
                        + 0.05 * transcoded_image_200_399
                        + 0.01 * transcoded_image_0_199
                        + transcoded_rest
                        + original
                    )

                    # skip if the size of the original is more than 4MB (grpc limit)
                    # if original_size > 4 * 1000 * 1000:
                    if original_size > 1 * 1000 * 1000:
                        continue

                    i = i + 1

                    # do ourselves a favor and replace weird characters
                    # alphanumeric and / . _ - only
                    basename_encoded = re.sub(r"[^a-zA-Z0-9/._-]", "", basename)

                    # write the lines to the output file if not 0
                    lines = []
                    if original > 0:
                        lines.append(
                            f"{basename_encoded},original,{int(original_size)},{original}\n"
                        )

                    if transcoded_image_1000 > 0:
                        lines.append(
                            f"{basename_encoded},1000,{int(original_size*0.25)},{transcoded_image_1000}\n"
                        )

                    if transcoded_image_800_999 > 0:
                        lines.append(
                            f"{basename_encoded},800_999,{int(original_size*0.2)},{transcoded_image_800_999}\n"
                        )

                    if transcoded_image_600_799 > 0:
                        lines.append(
                            f"{basename_encoded},600_799,{int(original_size*0.15)},{transcoded_image_600_799}\n"
                        )

                    if transcoded_image_400_599 > 0:
                        lines.append(
                            f"{basename_encoded},400_599,{int(original_size*0.1)},{transcoded_image_400_599}\n"
                        )

                    if transcoded_image_200_399 > 0:
                        lines.append(
                            f"{basename_encoded},200_399,{int(original_size*0.05)},{transcoded_image_200_399}\n"
                        )

                    if transcoded_image_0_199 > 0:
                        lines.append(
                            f"{basename_encoded},0_199,{int(original_size*0.01)},{transcoded_image_0_199}\n"
                        )

                    o_full.writelines(lines)
                    if i % 100 == 0:
                        o_reduced.writelines(lines)
