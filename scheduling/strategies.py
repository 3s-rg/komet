#!/usr/bin/env python3

import typing
import math

import tqdm

import celestial.types
import celestial.zip_serializer


class Strategy(typing.Protocol):
    def __init__(self): ...

    def init(self, ground_stations: typing.List[str], num_sats: int): ...

    def update(
        self,
        t: int,
        traffic_matrix: typing.List[typing.List[typing.Union[float, int]]],
        active: typing.List[bool],
    ): ...

    def sat_assignments(self) -> typing.List[typing.Tuple[str, int]]: ...


class MinMaxStrategy:
    def __init__(self, to_select: str):
        self.assignments: typing.List[typing.Tuple[str, int]] = []
        self.select_multple = to_select == "many"

    def init(self, ground_stations: typing.List[str], num_sats: int):
        self.ground_stations = ground_stations
        self.num_sats = num_sats

    def update(
        self,
        t: int,
        traffic_matrix: typing.List[typing.List[typing.Union[float, int]]],
    ):
        # first clear the assignments
        self.assignments = []

        # simply select the closest one for each
        if self.select_multple:
            for i, row in enumerate(traffic_matrix):
                min_idx = -1
                min_val = float("inf")
                for j, val in enumerate(row):
                    if val < min_val:
                        min_idx = j
                        min_val = val
                self.assignments.append((self.ground_stations[i], min_idx))

        else:
            # select the one with the lowest sum
            min_idx = -1
            min_val = float("inf")
            for j in range(self.num_sats):
                sum_val = sum([row[j] for row in traffic_matrix])
                if sum_val < min_val:
                    min_idx = j
                    min_val = sum_val

            for i in range(len(self.ground_stations)):
                self.assignments.append((self.ground_stations[i], min_idx))

    def sat_assignments(self) -> typing.List[typing.Tuple[str, int]]:
        return self.assignments

    def __str__(self):
        return f"minmax-{self.select_multple}"


class OneToOneStrategy:
    def __init__(self, threshold: float):
        self.assignment: typing.Optional[int] = None
        self.threshold = threshold

    def init(self, ground_stations: typing.List[str], num_sats: int):
        if len(ground_stations) > 1:
            raise ValueError("OneToOneStrategy only supports one ground station")
        self.ground_stations = ground_stations

    def update(
        self,
        t: int,
        traffic_matrix: typing.List[typing.List[typing.Union[float, int]]],
    ):
        min_idx = -1
        min_val = float("inf")
        for j, val in enumerate(traffic_matrix[0]):
            if val < min_val:
                min_idx = j
                min_val = val

        # if none is assigned to a ground station, assign the closest one
        # or if the assigned one is not active, assign the closest one
        if self.assignment is None:
            self.assignment = min_idx
            return

        # get the distance to the assigned satellite
        curr_dist = traffic_matrix[0][self.assignment]

        # figure out if it is better than threshold
        if min_val < (curr_dist * (1 - self.threshold)):
            # print(f"{min_val} < {curr_dist} * {1 - self.threshold}")
            self.assignment = min_idx
            return

    def sat_assignments(self) -> typing.List[typing.Tuple[str, int]]:
        if self.assignment is None:
            return []
        return [(self.ground_stations[0], self.assignment)]

    def __str__(self):
        return f"one2one-{self.threshold}"


class OneToOneAbsoluteStrategy:
    def __init__(
        self,
        absolute_threshold: int,
    ):
        self.assignment: typing.Optional[int] = None
        self.absolute_threshold = absolute_threshold

    def init(self, ground_stations: typing.List[str], num_sats: int):
        if len(ground_stations) > 1:
            raise ValueError("OneToOneStrategy only supports one ground station")
        self.ground_stations = ground_stations

    def update(
        self,
        t: int,
        traffic_matrix: typing.List[typing.List[typing.Union[float, int]]],
    ):
        min_idx = -1
        min_val = float("inf")
        for j, val in enumerate(traffic_matrix[0]):
            if val < min_val:
                min_idx = j
                min_val = val

        # if none is assigned to a ground station, assign the closest one
        # or if the assigned one is not active, assign the closest one
        if self.assignment is None:
            self.assignment = min_idx
            return

        # get the distance to the assigned satellite
        curr_dist = traffic_matrix[0][self.assignment]

        # figure out if it is better than threshold
        if min_val < curr_dist - self.absolute_threshold:
            # print(f"{min_val} < {curr_dist} * {1 - self.threshold}")
            self.assignment = min_idx
            return

    def sat_assignments(self) -> typing.List[typing.Tuple[str, int]]:
        if self.assignment is None:
            return []
        return [(self.ground_stations[0], self.assignment)]

    def __str__(self):
        return f"one2one-abs-{self.absolute_threshold}"


class ManyToOneStrategy:
    def __init__(
        self,
        threshold: float,
        agg: str,
    ):
        self.assignment: typing.Optional[int] = None
        self.threshold = threshold
        self.agg = agg

    def init(self, ground_stations: typing.List[str], num_sats: int):
        self.ground_stations = ground_stations
        self.num_sats = num_sats

    def update(
        self,
        t: int,
        traffic_matrix: typing.List[typing.List[typing.Union[float, int]]],
    ):
        min_idx = -1
        min_val = float("inf")

        for j in range(self.num_sats):
            score = (
                math.sqrt(sum([row[j] ** 2 for row in traffic_matrix]))
                if self.agg == "rmse"
                else sum([row[j] for row in traffic_matrix])
            )

            if score < min_val:
                min_idx = j
                min_val = score

        # if none is assigned to a ground station, assign the closest one
        # or if the assigned one is not active, assign the closest one
        if self.assignment is None:
            self.assignment = min_idx
            return

        # get the distance to the assigned satellite
        curr_dist = (
            math.sqrt(sum([row[self.assignment] ** 2 for row in traffic_matrix]))
            if self.agg == "rmse"
            else sum([row[self.assignment] for row in traffic_matrix])
        )

        # figure out if it is better than threshold
        if min_val < curr_dist * (1 - self.threshold):
            # print(f"{min_val} < {curr_dist} * {1 - self.threshold}")
            self.assignment = min_idx
            return

    def sat_assignments(self) -> typing.List[typing.Tuple[str, int]]:
        return [(g, self.assignment) for g in self.ground_stations]

    def __str__(self):
        return f"many2one-{self.agg}-{self.threshold}"


class ManyToManyStrategy:
    def __init__(self, threshold: float):
        self.assignments: typing.List[typing.Tuple[str, int]] = []
        self.threshold = threshold
        self.deployed_sats = set()

    def init(self, ground_stations: typing.List[str], num_sats: int):
        self.ground_stations = ground_stations

    def update(
        self,
        t: int,
        traffic_matrix: typing.List[typing.List[typing.Union[float, int]]],
    ):
        self.assignments = []

        closest_sets = {}
        for g in self.ground_stations:
            closest_sets[g] = set()
            min_val = float("inf")

            for i, s in enumerate(traffic_matrix[self.ground_stations.index(g)]):
                if s < min_val:
                    min_val = s

            for i, s in enumerate(traffic_matrix[self.ground_stations.index(g)]):
                if s < min_val * (1 + self.threshold):
                    closest_sets[g].add(i)

        # now we have the closest sets, we need to figure out the best assignment

        # this is from ChatGPT
        def find_hitting_set(sets: typing.List[typing.Set[int]]) -> typing.Set[int]:
            hitting_set = set()

            while len(sets) > 0:
                # Count the frequency of each element across all sets
                element_count: typing.Dict[int, int] = {}
                for s in sets:
                    for e in s:
                        if e in element_count:
                            element_count[e] += 1
                        else:
                            element_count[e] = 1

                # Find the elements with the highest frequency
                max_elements = [
                    k
                    for k, v in element_count.items()
                    if v == max(element_count.values())
                ]
                # tie breaker: if the sat is already deployed
                max_element = None
                for e in max_elements:
                    if e in self.deployed_sats:
                        max_element = e
                        break

                if max_element is None:
                    max_element = max_elements[0]

                # Add this element to the hitting set
                hitting_set.add(max_element)

                # Remove all sets that are covered by this element
                sets = [s for s in sets if max_element not in s]

            return hitting_set

        hitting_set = find_hitting_set(list(closest_sets.values()))

        # print(f"hitting_set of {[d for d in closest_sets.values()]} is {hitting_set}")

        # now find the best assignment
        for g in self.ground_stations:
            for s in closest_sets[g]:
                if s in hitting_set:
                    self.assignments.append((g, s))
                    self.deployed_sats.add(s)
                    break

    def sat_assignments(self) -> typing.List[typing.Tuple[str, int]]:
        return self.assignments

    def __str__(self):
        return f"many2many-{self.threshold}"


class ManyToManyAbsoluteStrategy:
    def __init__(self, absolute_threshold: int):
        self.assignments: typing.List[typing.Tuple[str, int]] = []
        self.absolute_threshold = absolute_threshold
        self.deployed_sats = set()

    def init(self, ground_stations: typing.List[str], num_sats: int):
        self.ground_stations = ground_stations

    def update(
        self,
        t: int,
        traffic_matrix: typing.List[typing.List[typing.Union[float, int]]],
    ):
        self.assignments = []

        closest_sets = {}
        for g in self.ground_stations:
            closest_sets[g] = set()
            min_val = float("inf")

            for i, s in enumerate(traffic_matrix[self.ground_stations.index(g)]):
                if s < min_val:
                    min_val = s

            for i, s in enumerate(traffic_matrix[self.ground_stations.index(g)]):
                if s - self.absolute_threshold < min_val:
                    closest_sets[g].add(i)

        # now we have the closest sets, we need to figure out the best assignment

        # this is from ChatGPT
        def find_hitting_set(sets: typing.List[typing.Set[int]]) -> typing.Set[int]:
            hitting_set = set()

            while len(sets) > 0:
                # Count the frequency of each element across all sets
                element_count: typing.Dict[int, int] = {}
                for s in sets:
                    for e in s:
                        if e in element_count:
                            element_count[e] += 1
                        else:
                            element_count[e] = 1

                # Find the elements with the highest frequency
                max_elements = [
                    k
                    for k, v in element_count.items()
                    if v == max(element_count.values())
                ]
                # tie breaker: if the sat is already deployed
                max_element = None
                for e in max_elements:
                    if e in self.deployed_sats:
                        max_element = e
                        break

                if max_element is None:
                    max_element = max_elements[0]

                # Add this element to the hitting set
                hitting_set.add(max_element)

                # Remove all sets that are covered by this element
                sets = [s for s in sets if max_element not in s]

            return hitting_set

        hitting_set = find_hitting_set(list(closest_sets.values()))

        # print(f"hitting_set of {[d for d in closest_sets.values()]} is {hitting_set}")

        # now find the best assignment
        for g in self.ground_stations:
            for s in closest_sets[g]:
                if s in hitting_set:
                    self.assignments.append((g, s))
                    self.deployed_sats.add(s)
                    break

    def sat_assignments(self) -> typing.List[typing.Tuple[str, int]]:
        return self.assignments

    def __str__(self):
        return f"many2many-abs-{self.absolute_threshold}"


class ManyToManyFixedStrategy:
    def __init__(
        self,
        threshold: float,
        max_sats: int,
    ):
        self.assignments: typing.List[typing.Tuple[str, int]] = []
        self.threshold = threshold
        self.deployed_sats = set()
        self.max_sats = max_sats

    def init(self, ground_stations: typing.List[str], num_sats: int):
        self.ground_stations = ground_stations

    def update(
        self,
        t: int,
        traffic_matrix: typing.List[typing.List[typing.Union[float, int]]],
    ):
        self.assignments = []

        closest_sets = {}
        for g in self.ground_stations:
            closest_sets[g] = set()
            min_val = float("inf")

            for i, s in enumerate(traffic_matrix[self.ground_stations.index(g)]):
                if s < min_val:
                    min_val = s

            for i, s in enumerate(traffic_matrix[self.ground_stations.index(g)]):
                if s < min_val * (1 + self.threshold):
                    closest_sets[g].add(i)

        # now we have the closest sets, we need to figure out the best assignment

        # this is from ChatGPT
        def find_hitting_set(sets: typing.List[typing.Set[int]]) -> typing.Set[int]:
            hitting_set = set()

            while len(sets) > 0:
                # Count the frequency of each element across all sets
                element_count: typing.Dict[int, int] = {}
                for s in sets:
                    for e in s:
                        if e in element_count:
                            element_count[e] += 1
                        else:
                            element_count[e] = 1

                # Find the elements with the highest frequency
                max_elements = [
                    k
                    for k, v in element_count.items()
                    if v == max(element_count.values())
                ]
                # tie breaker: if the sat is already deployed
                max_element = None
                for e in max_elements:
                    if e in self.deployed_sats:
                        max_element = e
                        break

                if max_element is None:
                    max_element = max_elements[0]

                # Add this element to the hitting set
                hitting_set.add(max_element)

                # Remove all sets that are covered by this element
                sets = [s for s in sets if max_element not in s]

                if len(hitting_set) >= self.max_sats:
                    break

            return hitting_set

        hitting_set = find_hitting_set(list(closest_sets.values()))

        # print(f"hitting_set of {[d for d in closest_sets.values()]} is {hitting_set}")

        # now find the best assignment
        for g in self.ground_stations:
            for s in closest_sets[g]:
                if s in hitting_set:
                    self.assignments.append((g, s))
                    self.deployed_sats.add(s)
                    break

    def sat_assignments(self) -> typing.List[typing.Tuple[str, int]]:
        return self.assignments

    def __str__(self):
        return f"many2many-fixed-{self.threshold}-{self.max_sats}"


class StickyStrategy:
    def __init__(
        self,
        trajectory_file: str,
    ):
        self.assignments = []

        self.traj_file = trajectory_file

        # these are static in the paper
        self.latency_threshold = 0.1
        self.candidate_number = 5

        self.debug = False

    def init(self, ground_stations: typing.List[int], num_sats: int):
        self.ground_stations = ground_stations
        self.num_sats = num_sats

        self.serializer = celestial.zip_serializer.ZipDeserializer(self.traj_file)

        # we must now load the entire trajectory data
        config = self.serializer.config()
        duration = config.duration
        resolution = config.resolution

        seen_traffic = []

        def _get_next_traffic_matrix():
            sat_base_matrix = [
                [float("inf") for _ in range(num_sats)] for _ in range(num_sats)
            ]
            for i in range(num_sats):
                sat_base_matrix[i][i] = 0

            gst_base_matrix = [
                [float("inf") for _ in range(num_sats)]
                for _ in range(len(ground_stations))
            ]

            for t in range(0, duration, resolution):
                real_t = t + config.offset

                links = self.serializer.diff_links(real_t)

                for link in links:
                    if celestial.types.MachineID_group(link[0]) == 0:
                        if celestial.types.MachineID_group(link[1]) == 0:
                            continue

                        if celestial.types.MachineID_id(link[0]) not in ground_stations:
                            # print(
                            #     f"skipping {celestial.types.MachineID_id(link[0])} to {celestial.types.MachineID_id(link[1])}"
                            # )
                            continue

                        # we only care about satellites here
                        gst_base_matrix[
                            ground_stations.index(celestial.types.MachineID_id(link[0]))
                        ][celestial.types.MachineID_id(link[1])] = (
                            celestial.types.Link_latency_us(link[2])
                            if not celestial.types.Link_blocked(link[2])
                            else float("inf")
                        )
                    else:
                        sat_base_matrix[celestial.types.MachineID_id(link[0])][
                            celestial.types.MachineID_id(link[1])
                        ] = (
                            celestial.types.Link_latency_us(link[2])
                            if not celestial.types.Link_blocked(link[2])
                            else float("inf")
                        )

                        sat_base_matrix[celestial.types.MachineID_id(link[1])][
                            celestial.types.MachineID_id(link[0])
                        ] = (
                            celestial.types.Link_latency_us(link[2])
                            if not celestial.types.Link_blocked(link[2])
                            else float("inf")
                        )

                yield (
                    [[x for x in row] for row in sat_base_matrix],
                    [[x for x in row] for row in gst_base_matrix],
                    t,
                )

        traffic_gen = _get_next_traffic_matrix()

        def get_traffic_at_time(t):
            if t < len(seen_traffic):
                return seen_traffic[t]

            while len(seen_traffic) <= t:
                seen_traffic.append(next(traffic_gen))

            return seen_traffic[t]

        def trim_cache(t):
            for i in range(t):
                seen_traffic[i] = None

        # we just simulate everything ahead of time
        # as a first step, we start at 0 to get the first assignment
        minmax = float("inf")
        minval = None
        curr_traffic, curr_gst_traffic, traffic_time = get_traffic_at_time(0)
        assert traffic_time == 0

        for j in range(self.num_sats):
            sum_val = sum([row[j] for row in curr_gst_traffic])
            # print(f"sum_val for {j} is {sum_val}")
            if sum_val < minmax:
                minmax = sum_val
                minval = j

        self.assignments.append(minval)

        # now, we perform the heuristic
        # note that our implementation is slightly different from the paper
        # because the paper assumes infinite recursion? doesn't make sense in practice
        # instead of taking successor latency into account, we just take predecessor latency
        t = 1

        progress_bar = tqdm.tqdm(total=duration, desc="sticky init")

        while t < duration:
            progress_bar.update(t - progress_bar.n)

            if self.debug:
                print(f"evaluating time stamp {t}")

            # to save storage, trim the traffic cache
            trim_cache(t - 1)

            if self.debug:
                print(len(self.assignments))
            assert t == len(self.assignments)

            curr_traffic, curr_gst_traffic, traffic_time = get_traffic_at_time(t)
            if self.debug:
                print(f"got traffic at {traffic_time}")
            assert traffic_time == t

            # compute the minmax
            minmax = float("inf")
            for j in range(self.num_sats):
                sum_val = sum([row[j] for row in curr_gst_traffic])
                if sum_val < minmax:
                    minmax = sum_val

            if self.debug:
                print(f"minmax is {minmax}")

            # (1) Compute the set of meetup-servers that provide latency within 10% of MinMax
            candidates = []
            for j in range(self.num_sats):
                sum_val = sum([row[j] for row in curr_gst_traffic])
                if sum_val <= minmax * (1 + self.latency_threshold):
                    candidates.append(j)

            if self.debug:
                print(f"found {len(candidates)} candidates")

            # (2) For each of these candidate meetup-servers, compute the time until the next hand-off. Pick the 5 candidates with the longest time until a hand-off.
            future_candidates = []

            for i in candidates:
                if self.debug:
                    print(f"evaluating candidate {i}")
                # we need to look ahead
                timestep = 1
                for timestep in range(1, duration - t):
                    future_traffic = get_traffic_at_time(t + timestep)
                    # compute the minmax at this point
                    minmax = float("inf")
                    for x in range(self.num_sats):
                        sum_val = sum([row[x] for row in future_traffic[1]])
                        if sum_val < minmax:
                            minmax = sum_val

                    # figure out if the candidate is still in the threshold
                    if sum([row[i] for row in future_traffic[1]]) > minmax * (
                        1 + self.latency_threshold
                    ):
                        # we can't use this candidate anymore!
                        break

                # we can't use this candidate anymore!
                future_candidates.append((i, timestep))
                if self.debug:
                    print(f"candidate {i} is out at {t + timestep}")

                if len(future_candidates) >= self.candidate_number:
                    # some logic to update the progress bar
                    min_update = min(
                        sorted(future_candidates, key=lambda x: x[1], reverse=True)[:5],
                        key=lambda x: x[1],
                    )
                    progress_bar.update(t + min_update[1] - progress_bar.n)

            # now pick 5 of these with the highest time
            future_candidates.sort(key=lambda x: x[1], reverse=True)
            future_candidates = future_candidates[: self.candidate_number]

            if self.debug:
                print(f"picked {len(future_candidates)} future candidates")

            # (3) Among these 5, pick one which would result in the least latency for hand-off to its successor.
            # (here we differ a bit by looking at the current one)
            minval = float("inf")
            mincandidate = None
            for i in future_candidates:
                if curr_traffic[i[0]][self.assignments[t - 1]] < minval:
                    minval = curr_traffic[i[0]][self.assignments[t - 1]]
                    mincandidate = i

            if self.debug:
                print(f"picked {mincandidate[0]} until {t + mincandidate[1]}")

            # now we know that we can keep this assignment for a while
            self.assignments.extend([mincandidate[0]] * mincandidate[1])
            t += mincandidate[1]

        assert t == duration
        assert len(self.assignments) == duration

        progress_bar.close()
        self.serializer.close()

    def update(
        self,
        t: int,
        traffic_matrix: typing.List[typing.List[typing.Union[float, int]]],
    ):
        self.t = t

    def sat_assignments(self) -> typing.List[typing.Tuple[str, int]]:
        return [(g, self.assignments[self.t]) for g in self.ground_stations]

    def __str__(self):
        return "sticky"
