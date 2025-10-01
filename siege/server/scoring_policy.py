#!/usr/bin/python3
# -*- coding: utf8 -*-
#
# Siege Competition Framework
#
# Author: Dmitriy Beryoza (0xd13a)

from siege.core.attack_result import AttackResult
from siege.core.tick_results import TickResults
from siege.server.server_config import ServerConfig


class TargetScore:
    empty_result: bool
    benign_success_count: int
    benign_failure_count: int
    malicious_success_count: int
    malicious_failure_count: int
    service_down_count: int
    ignored_benign_successes: int
    ignored_malicious_failures: int
    caps_reached: int
    score_delta: int

    def __init__(
            self, empty_result: bool, benign_success_count: int = 0,
            benign_failure_count: int = 0, malicious_success_count: int = 0,
            malicious_failure_count: int = 0, service_down_count: int = 0,
            ignored_benign_successes: int = 0,
            ignored_malicious_failures: int = 0, caps_reached: int = 0,
            score_delta: int = 0) -> None:
        self.empty_result = empty_result
        self.benign_success_count = benign_success_count
        self.benign_failure_count = benign_failure_count
        self.malicious_success_count = malicious_success_count
        self.malicious_failure_count = malicious_failure_count
        self.service_down_count = service_down_count
        self.ignored_benign_successes = ignored_benign_successes
        self.ignored_malicious_failures = ignored_malicious_failures
        self.caps_reached = caps_reached
        self.score_delta = score_delta


class PreparedScore:

    tick: int
    tick_score: int
    tick_since: int
    target_scores: dict[int, TargetScore]

    def __init__(self, tick: int, tick_score: int, tick_since: int) -> None:
        self.tick = tick
        self.tick_score = tick_score
        self.tick_since = tick_since
        self.target_scores = {}

    def add_target_score(self, target_id: int,
                         target_score: TargetScore) -> None:
        self.target_scores[target_id] = target_score

    def get_tick(self) -> int:
        return self.tick

    def get_tick_score(self) -> int:
        return self.tick_score

    def get_tick_since(self) -> int:
        return self.tick_since

    def get_target_scores(self) -> dict[int, TargetScore]:
        return self.target_scores


class ScoringPolicy:

    received_results: dict[int, list[TickResults]]
    config: ServerConfig

    def __init__(self, config: ServerConfig,
                 received_results: dict[int, list[TickResults]]) -> None:
        self.config = config
        self.received_results = received_results

    def calculate_scores(self, team_id: int) -> list[PreparedScore]:
        """ Calculate all scores based on current data """
        prepared_scores: list[PreparedScore] = []

        # Set up an overall negative cap. The negative score for the team will
        # not go below this number.
        negative_score_cap = self.config.get_negative_score_cap() * \
            len(self.config.get_target_ids())

        tick_score = 0

        # Initialize summary score values
        summary_scores: dict[int, list[int]] = {}
        for target_id in self.config.get_target_ids():
            summary_scores[target_id] = [0] * \
                self.config.get_target(target_id).get_vulns()

        # Keep track of since when we kept this score
        tick_since = 0
        last_score = 0

        # For every tick
        for tick in range(len(self.received_results[team_id])):
            tick_results = self.received_results[team_id][tick]

            target_scores: dict[int, TargetScore] = {}

            # For every service
            for target_id in tick_results.get_results().keys():
                target_results = tick_results.get_target_results(target_id)

                benign_success_count = 0
                benign_failure_count = 0
                malicious_success_count = 0
                malicious_failure_count = 0
                service_down_count = 0

                # Initialize delta score values for the current tick
                vulns = self.config.get_target(target_id).get_vulns()
                tick_scores = [0]*vulns
                benign_successes = [0]*vulns

                # For every result for the service
                for res in target_results:
                    vuln_id = res.get_request_id()

                    if vuln_id > 0:
                        vuln_idx = vuln_id-1
                        if res.get_result() == AttackResult.RESULT_SUCCESS:
                            tick_scores[vuln_idx] += \
                                self.config.get_successful_benign_points()
                            benign_successes[vuln_idx] += 1
                            benign_success_count += 1

                        if res.get_result() == AttackResult.RESULT_FAILURE:
                            tick_scores[vuln_idx] -= \
                                self.config.get_failed_benign_points()
                            benign_failure_count += 1

                        if res.get_result() == AttackResult.RESULT_DOWN:
                            tick_scores[vuln_idx] -= \
                                self.config.get_down_points()
                            service_down_count += 1
                    else:
                        vuln_idx = -vuln_id-1
                        if res.get_result() == AttackResult.RESULT_SUCCESS:
                            tick_scores[vuln_idx] -= \
                                self.config.get_successful_malicious_points()
                            malicious_success_count += 1

                        if res.get_result() == AttackResult.RESULT_FAILURE:
                            tick_scores[vuln_idx] += \
                                self.config.get_failed_malicious_points()
                            malicious_failure_count += 1

                        if res.get_result() == AttackResult.RESULT_DOWN:
                            tick_scores[vuln_idx] -= \
                                self.config.get_down_points()
                            service_down_count += 1

                tick_delta = 0
                caps_reached = 0

                ignored_benign_successes = 0
                ignored_malicious_failures = 0

                # Cap the results per vulnerability and build the total
                for vuln_id in range(len(summary_scores[target_id])):

                    expected_sum = summary_scores[target_id][vuln_id] + \
                        tick_scores[vuln_id]
                    if expected_sum > self.config.get_score_cap():
                        # print("### +CAP REACHED {} {} {} {}".
                        # format(tick, service_id,
                        # summary_scores[service_id][vuln_id],
                        # tick_scores[vuln_id]))
                        tick_scores[vuln_id] = self.config.get_score_cap() - \
                            summary_scores[target_id][vuln_id]

                        # Calculate the scores we need to ignore because the
                        # cap was reached
                        ignored_scores = int((expected_sum -
                                             self.config.get_score_cap()) //
                                             self.config.
                                             get_successful_benign_points())

                        # Distribute ignored scores between benign successes
                        # and malicious failures because we show them on the
                        # scoreboard as separate numbers
                        if ignored_scores < benign_successes[vuln_id]:
                            benign_diff = ignored_scores
                            malicious_diff = 0
                        else:
                            benign_diff = benign_successes[vuln_id]
                            malicious_diff = ignored_scores - benign_diff

                        ignored_benign_successes += benign_diff
                        benign_success_count -= benign_diff

                        ignored_malicious_failures += malicious_diff
                        malicious_failure_count -= malicious_diff

                    summary_scores[target_id][vuln_id] += tick_scores[vuln_id]

                    # Count positive caps reached
                    if summary_scores[target_id][vuln_id] == \
                            self.config.get_score_cap():
                        caps_reached += 1

                    tick_delta += tick_scores[vuln_id]

                # print("### DELTA {} {} {}".format(tick, service_id,
                # str(tick_scores)))

                target_scores[target_id] = TargetScore(
                    len(target_results) == 0,
                    benign_success_count, benign_failure_count,
                    malicious_success_count, malicious_failure_count,
                    service_down_count, ignored_benign_successes,
                    ignored_malicious_failures, caps_reached, tick_delta)

                tick_score += tick_delta

            # Adjust accumulated score if it goes below negative score cap
            if tick_score < negative_score_cap:
                tick_score = negative_score_cap

            # Update last tick since the score has been seen, if necessary
            if tick_score != last_score:
                last_score = tick_score
                tick_since = tick

            # print("$$$ {} {} {}".format(tick, tick_score, tick_since))
            prepared_score = PreparedScore(tick, tick_score, tick_since)
            for target_id in sorted(self.config.get_target_ids()):
                if target_id in target_scores.keys():
                    prepared_score.add_target_score(target_id,
                                                    target_scores[target_id])
                else:
                    prepared_score.add_target_score(target_id,
                                                    TargetScore(True))

            prepared_scores.append(prepared_score)

        return prepared_scores
