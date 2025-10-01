#!/usr/bin/python3
# -*- coding: utf8 -*-
#
# Siege Competition Framework
#
# Author: Dmitriy Beryoza (0xd13a)

import json
import time
from typing import Any
import requests
import random
from threading import Thread
import traceback

from siege.attacker.attacker import Attacker
from siege.bot.bot_result_db import BotResultDB
from siege.bot.bot_config import BotConfig
from siege.core.log import log, log_error
from siege.core.attack_result import AttackResult
from siege.core.tick_results import TickResults
from siege.core.security import Security

RESULTS_API = "results"
COMMAND_API = "command"

SLEEP_TIME = 5         # Sleep time for main loop


class Bot:

    bot_config: BotConfig
    bot_result_db: BotResultDB

    def __init__(self, bot_config: BotConfig) -> None:
        self.bot_config = bot_config
        self.bot_result_db = BotResultDB(self.bot_config.get_result_db_name())

    def run_attacks_on_target(self, target_id: int, attacker: Attacker,
                              tick: int, schedule: list[int],
                              results: TickResults) -> None:
        """ Thread to run attacks in. """
        try:
            # For every request
            for i in range(len(schedule)):
                request_id = schedule[i]
                # Are we sending a benign request?
                result = None
                if request_id > 0:
                    try:
                        log("[{}, tick {}] Sending benign request {}".
                            format(attacker.get_name(), tick, request_id))
                        result = attacker.benign_request(request_id, tick, i)
                        log("[{}, tick {}] Benign request {}, result: {}".
                            format(attacker.get_name(), tick, request_id,
                                   result))
                    except BaseException:
                        log_error("[{}, tick {}] Benign request {} failed: {}".
                                  format(attacker.get_name(), tick, request_id,
                                         traceback.format_exc()))
                        result = AttackResult.RESULT_DOWN
                else:
                    try:
                        log("[{}, tick {}] Sending malicious request {}".
                            format(attacker.get_name(), tick, -request_id))
                        result = attacker.malicious_request(-request_id, tick,
                                                            i)
                        log("[{}, tick {}] Malicious request {}, result: {}".
                            format(attacker.get_name(), tick, -request_id,
                                   result))
                    except BaseException:
                        log_error("[{}, tick {}] Malicious request {} "
                                  "failed: {}".format(attacker.get_name(),
                                                      tick, -request_id,
                                                      traceback.format_exc()))
                        result = AttackResult.RESULT_DOWN

                results.record(target_id, request_id, result)
        except BaseException:
            log_error("[{}, tick {}] Error producing results: {}".
                      format(attacker.get_name(), tick,
                             traceback.format_exc()))

    def run_attacks(self, tick: int) -> TickResults:
        """ Run randomized attacks. """

        full_result: TickResults = TickResults(self.bot_config.get_team_id(),
                                               tick)
        threads: dict[int, Thread] = {}

        # Initialize threads to run attacks on each service in parallel
        for target_id in self.bot_config.get_target_ids():
            threads[target_id] = Thread(
                target=self.run_attacks_on_target,
                args=(target_id, self.bot_config.get_attacker(target_id),
                      tick, self.bot_config.get_schedule(target_id, tick),
                      full_result,))

        # Start each thread
        for target_id in self.bot_config.get_target_ids():
            log("[{}, tick {}] Running attacks".format(
                self.bot_config.get_attacker(target_id).get_name(), tick))
            threads[target_id].start()

        # Wait for each thread to finish
        for target_id in self.bot_config.get_target_ids():
            threads[target_id].join()
            log("[{}, tick {}] Finished attacks".
                format(self.bot_config.get_attacker(target_id).get_name(),
                       tick))

        log("[tick {}] Full result: {}".format(tick, full_result))
        return full_result

    def server_request(self, api: str, payload: dict[str, Any],
                       report_error: bool = True) -> dict[str, Any] | None:
        try:
            # Sign the payload and encode the signature
            if self.bot_config.get_verify_signatures():
                enc_sig = Security.sign(json.dumps(payload, sort_keys=True),
                                    self.bot_config.get_key())
                headers = {"Signature": enc_sig,
                    "Content-Type": "application/json"}
            else:
                headers = {"Content-Type": "application/json"}
                
            result = requests.post("{}/{}/{}".format(
                self.bot_config.get_server(), api,
                self.bot_config.get_team_id()),
                headers=headers,
                json=payload,
                verify=self.bot_config.get_verify_server())

            if result.status_code != 200:
                log_error("HTTP error {} sending request to scoreboard".
                          format(result.status_code))
                return None
            if not isinstance(result.json(), dict):
                log_error("Result received from the server is "
                          "not a dictionary")
                return None

            if self.bot_config.get_verify_signatures():
                signature = result.headers.get("Signature", None)
                if signature is None:
                    log_error("No signature specified for response document")
                    return None

                if not Security.verify_signature(
                        json.dumps(result.json(), sort_keys=True), signature,
                        self.bot_config.get_server_key()):
                    log_error("Server response fails verification")
                    return None
            return result.json()
        except BaseException:
            if report_error:
                log_error("Error sending request to server API '{}': {}".
                          format(api, traceback.format_exc()))
            return None

    def ping_server(self) -> None:
        # Sign the payload and encode the signature
        payload: dict[str, Any] = {}
        payload["request"] = "ping"
        payload["team_id"] = self.bot_config.get_team_id()

        result = self.server_request(COMMAND_API, payload)

        if result is not None:
            log("Server ping succeeded")

    def get_config(self, report_error: bool) -> bool:
        # Sign the payload and encode the signature
        payload: dict[str, Any] = {}
        payload["request"] = "get_config"
        payload["team_id"] = self.bot_config.get_team_id()

        result = self.server_request(COMMAND_API, payload, report_error)

        if result is not None:
            try:
                self.bot_config.load_config(result["config"])
                log("Loaded dynamic configuration: {}".
                    format(json.dumps(result)))
                return True
            except Exception:
                log_error("Error loading dynamic configuration: {}\n{}".
                          format(json.dumps(result), traceback.format_exc()))
        return False

    def submit_result(self, tick: int, results: TickResults) -> None:
        """ Submit result to scoreboard. """

        payload = results.to_dict()
        # Sign the payload and encode the signature
        result = self.server_request(RESULTS_API, payload)
        if result is None:
            log_error("Error submitting results to server: {}".format(results))
        else:
            log("Submitted results to server: {}".format(results))

        self.bot_result_db.mark_tick_result_sent(tick)

    def submit_unsent_results(self) -> None:
        """ Send results that were not yet sent. """

        rows = self.bot_result_db.load_unsent_results()

        # Load results; if some have not been sent scoreboard must have been
        # offline for some reason
        for row in rows:
            self.submit_result(row[0], json.loads(row[1]))

    def run(self) -> None:
        """ Global loop. """
        print("Bot is running")

        random.seed(0)

        report_config_error = True
        current_tick = -1
        while True:
            if self.bot_config.is_configured():
                if self.bot_config.event_finished():
                    log("Event finished")
                    self.submit_unsent_results()
                    break

                # TODO: Disabling pings to reduce load on the server,
                # re-enable after Gunicorn fix
                # self.ping_server()

                if not self.bot_config.event_started():
                    log("Event not started")
                else:
                    self.submit_unsent_results()
                    tick = self.bot_config.get_tick()
                    if tick > current_tick:
                        current_tick = tick
                        full_result = self.run_attacks(tick)
                        self.bot_result_db.save_result(tick, full_result)
                        self.submit_result(tick, full_result)
            else:
                # Load config if necessary, but stop spamming the logs if
                # unsuccessful
                if not self.get_config(report_config_error):
                    report_config_error = False

            time.sleep(SLEEP_TIME)
