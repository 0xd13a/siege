#!/usr/bin/python3
# -*- coding: utf8 -*-
#
# Siege Competition Framework
#
# Author: Dmitriy Beryoza (0xd13a)

from datetime import datetime, timezone
import yaml
from pathlib import Path
import random
from typing import Any
from Crypto.PublicKey import RSA

from siege.attacker.attacker import Attacker
from siege.core.log import log
from siege.core.schemas import BOT_CONFIG_SCHEMA, verify_schema
from siege.core.security import Security
from siege.core.util import (clear_folder, fatal_error, load_class,
                             make_folder, is_ip_address, is_localhost)

DATA_FOLDER_NAME = "data/"
LOG_FOLDER_NAME = "logs/"

CONFIG_FOLDER_NAME = "config/"
BOT_CONFIG_FILE_MASK = "bot-config-*.yaml"
DEFAULT_CONFIG_FILE = CONFIG_FOLDER_NAME + BOT_CONFIG_FILE_MASK


class BotConfig:

    team_id: int         # Current team ID
    server: str
    key: RSA.RsaKey
    server_key: RSA.RsaKey

    start_time: datetime
    end_time: datetime        # Competition end time
    tick_length: int
    attackers: dict[int, Attacker]
    schedules: dict[int, list[list[int]]]  # Schedules of request execution

    remote_config_delivered: bool

    base_folder: Path
    verify_server: bool
    verify_signatures: bool

    def __init__(self) -> None:
        self.remote_config_delivered = False

    def is_configured(self) -> bool:
        return self.remote_config_delivered

    def get_base_folder(self) -> Path:
        return self.base_folder

    def set_base_folder(self, folder: Path) -> None:
        # Verify base folder
        if not folder.exists() or not folder.is_dir():
            fatal_error("Base folder not valid: {}".format(folder))

        self.base_folder = folder

    def get_data_folder(self) -> Path:
        data_folder = self.get_base_folder() / DATA_FOLDER_NAME

        make_folder(data_folder)

        return data_folder

    def get_log_folder(self) -> Path:
        log_folder = self.get_base_folder() / LOG_FOLDER_NAME

        make_folder(log_folder)

        return log_folder

    def get_team_id(self) -> int:
        return self.team_id

    def get_key(self) -> RSA.RsaKey:
        return self.key

    def get_server_key(self) -> RSA.RsaKey:
        return self.server_key

    def get_attacker(self, target_id: int) -> Attacker:
        return self.attackers[target_id]

    def get_schedule(self, target: int, tick: int) -> list[int]:
        return self.schedules[target][tick]

    def get_target_ids(self) -> list[int]:
        return sorted(self.attackers.keys())

    def get_verify_server(self) -> bool:
        return self.verify_server

    def get_verify_signatures(self) -> bool:
        return self.verify_signatures

    def get_server(self) -> str:
        return self.server

    def get_result_db_name(self) -> Path:
        return self.get_data_folder() / "results{}.db".format(self.team_id)

    def get_tick(self) -> int:
        """ Find out current tick. """
        if not self.event_started():
            return -1
        if self.event_finished():
            return -1
        return int((datetime.now(timezone.utc) -
                    self.start_time).total_seconds() //
                   self.tick_length)

    def event_started(self) -> bool:
        """ Has competition started? """
        return datetime.now(timezone.utc) >= self.start_time

    def event_finished(self) -> bool:
        """ Has competition finished? """
        return datetime.now(timezone.utc) >= self.end_time

    def get_total_ticks(self) -> int:
        return int((self.end_time - self.start_time).total_seconds()) // \
            self.tick_length

    def load_initial_config(self, filename: str | None = None) -> None:
        """ Load configuration data. """

        if filename is None:
            files = Path(self.base_folder).glob(DEFAULT_CONFIG_FILE)
            file = next(files, None)

            if file is None:
                fatal_error("Could not find config file that matches '{}'".
                            format(DEFAULT_CONFIG_FILE))
            config_file = str(file)
        else:
            # If specified, load another configuration file
            config_file = filename

        print("Initializing bot from config file '{}'".format(config_file))

        # Load config file
        f = open(config_file, "r")
        config = yaml.safe_load(f)

        # Validate bot configuration
        try:
            verify_schema(BOT_CONFIG_SCHEMA, config)
        except Exception as e:
            fatal_error("Error validating config file '{}'".format(filename),
                        e)

        self.team_id = config["id"]

        # Load signing key
        self.key = Security.import_key(config["key"])
        self.server_key = Security.import_key(config["server_key"])

        self.server = config["server"]

        # Check if we need to verify server's TLS certificate. Do not verify
        # when it's an IP address
        if is_ip_address(self.server):
            self.verify_server = False
            log("Not verifying server TLS certificate because server address is an IP")
        else:
            self.verify_server = True

        # Check if we need to verify signatures. Do not verify
        # when it's running locally, because we build keys as a separate 
        # step, externally
        if is_localhost(self.server):
            log("Not verifying request signatures because we are running locally")
            self.verify_signatures = False
        else:
            self.verify_signatures = True

    def load_config(self, config: dict[str, Any]) -> None:
        self.start_time = datetime.fromisoformat(config["start_time"])
        self.end_time = datetime.fromisoformat(config["end_time"])
        self.tick_length = config["tick_length"]

        self.attackers = {}
        self.schedules = {}

        # Load vulnerable service information
        for target in config["services"]:
            target_id = target["id"]

            cls = load_class(target["folder"], target["file"], target["class"])
            (host, port) = target["address"].split(":")
            log("Loading " + target["file"])
            try:
                cls_instance = cls(host, int(port))
            except Exception as e:
                fatal_error("Could not locate class " + target["class"], e)
            self.attackers[target_id] = cls_instance

            # Load request schedule information
            vulns = target["vulns"]
            per_tick = target["requests"]["per_tick"]

            defined_schedules: dict[int, list[int]] = {}
            schedule = target["requests"]["schedule"]
            for sched in schedule:
                tick = sched["tick"]
                req_values = sched["set"]

                if len(req_values) != per_tick:
                    fatal_error("Incorrect number of requests in a schedule "
                                "'{}', expected {}".format(req_values,
                                                           str(per_tick)))

                req_set = []

                for val in req_values:
                    int_val = int(val)

                    if (int_val == 0) or (abs(int_val) > vulns):
                        fatal_error("Incorrect request ID '{}', max is {}".
                                    format(str(int_val), str(vulns)))

                    req_set.append(int_val)

                defined_schedules[tick] = req_set

            sorted_defined_schedules = dict(sorted(defined_schedules.items()))

            # Now we have a sorted list of individual schedules, build a
            # schedule for every tick

            # Check that we have the schedule for the "tick 0", at the very
            # least
            if len(sorted_defined_schedules) == 0 or \
                    (0 not in sorted_defined_schedules):
                fatal_error("No schedule defined to tick 0")

            self.schedules[target_id] = []

            for tick in range(self.get_total_ticks()):
                if tick in sorted_defined_schedules:
                    sched_copy = sorted_defined_schedules[tick]
                else:
                    random.shuffle(sched_copy)
                self.schedules[target_id].append(sched_copy.copy())

        self.remote_config_delivered = True

    def clear_results(self) -> None:
        clear_folder(self.get_data_folder())
