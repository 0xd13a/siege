#!/usr/bin/python3
# -*- coding: utf8 -*-
#
# Siege Competition Framework
#
# Author: Dmitriy Beryoza (0xd13a)

from siege.core.schemas import (SERVER_CONFIG_SCHEMA, SERVICES_CONFIG_SCHEMA,
                                TEAMS_CONFIG_SCHEMA, KEYS_CONFIG_SCHEMA,
                                verify_schema)
from siege.core.security import Security
from siege.core.team import Team
from siege.core.target import Target
from siege.core.util import (fatal_error, get_sorted_values, time_diff,
                             make_folder, clear_folder, is_localhost,
                             is_ip_address)
from datetime import datetime, timedelta, timezone
from pathlib import Path
import yaml
import json
from Crypto.PublicKey import RSA
from typing import Any

CONFIG_DB = "server_config.db"

CONFIG_FOLDER_NAME = "config/"
DATA_FOLDER_NAME = "data/"
LOG_FOLDER_NAME = "logs/"
SOURCE_SITE_FOLDER_NAME = "site/"
#SERVER_CONFIG_FILE = "server_config.yaml"

#BOT_CONFIG_FOLDER_NAME = "bots/"

DEFAULT_CONFIG_FILE = CONFIG_FOLDER_NAME + "config.yaml"
DEFAULT_SERVICES_FILE = CONFIG_FOLDER_NAME + "services.yaml"
TEAMS_CONFIG_FILE = CONFIG_FOLDER_NAME + "teams.yaml"
KEYS_CONFIG_FILE = CONFIG_FOLDER_NAME + "keys.yaml"

BOT_CONFIG_FILE_NAME = "bot-config-{}.yaml"

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 65500
DEFAULT_ADDRESS = "{}:{}".format(DEFAULT_HOST, DEFAULT_PORT)


class ServerConfig:

    start_time: datetime
    duration: int
    prep_minutes: int
    tick_length: int
    server: str
    site_folder: Path    # Folder to put the generated HTML files into
    score_cap: int
    negative_score_cap: int
    successful_benign_points: int
    failed_benign_points: int
    successful_malicious_points: int
    failed_malicious_points: int
    down_points: int

    server_signing_key: RSA.RsaKey

    teams: dict[int, Team]
    targets: dict[int, Target]

    base_folder: Path

    use_gunicorn: bool
    address_host: str
    address_port: int
    tls_cert_file: str
    tls_key_file: str
    verify_signatures: bool
    verify_server: bool


    def __init__(self) -> None:
        pass

    def get_base_folder(self) -> Path:
        return self.base_folder

    def set_base_folder(self, folder: Path) -> None:
        # Verify base folder
        if not folder.exists() or not folder.is_dir():
            fatal_error("Base folder not valid: {}".format(folder))

        self.base_folder = folder

    def get_log_folder(self) -> Path:
        log_folder = self.get_base_folder() / LOG_FOLDER_NAME

        make_folder(log_folder)

        return log_folder

    def get_data_folder(self) -> Path:
        data_folder = self.get_base_folder() / DATA_FOLDER_NAME

        make_folder(data_folder)

        return data_folder
    """
    def get_bot_config_folder(self) -> Path:
        bot_folder = self.get_base_folder() / CONFIG_FOLDER_NAME / \
            BOT_CONFIG_FOLDER_NAME

        make_folder(bot_folder)

        return bot_folder
    """

    #def get_server_config_file(self) -> Path:
    #    return Path(self.get_data_folder()) / SERVER_CONFIG_FILE

    def get_source_site_folder(self) -> Path:
        source_site_folder = self.get_base_folder() / SOURCE_SITE_FOLDER_NAME

        make_folder(source_site_folder)

        return source_site_folder

    def get_key(self) -> RSA.RsaKey:
        return self.server_signing_key

    def get_team(self, id: int) -> Team:
        return self.teams[id]

    def get_team_ids(self) -> list[int]:
        return sorted(self.teams.keys())

    def get_team_num(self) -> int:
        return len(self.teams)

    def get_teams(self) -> list[Team]:
        return get_sorted_values(self.teams)

    def get_target(self, target_id: int) -> Target:
        return self.targets[target_id]

    def get_targets(self) -> list[Target]:
        return get_sorted_values(self.targets)

    def get_target_ids(self) -> list[int]:
        return sorted(self.targets.keys())

    def get_site_folder(self) -> Path:
        return self.site_folder

    def get_start_time(self) -> datetime:
        return self.start_time

    def tick2time(self, tick: int) -> datetime:
        """ Convert tick to corresponding timestamp. """
        return self.start_time + timedelta(seconds=(tick * self.tick_length))

    def get_end_time(self) -> datetime:
        return self.start_time + timedelta(minutes=self.duration)

    def get_prep_minutes(self) -> int:
        return self.prep_minutes

    def get_prep_start(self) -> datetime:
        return self.start_time - timedelta(minutes=self.prep_minutes)

    def get_tick_length(self) -> int:
        return self.tick_length

    def get_total_ticks(self) -> int:
        return (self.duration * 60) // self.tick_length

    def get_score_cap(self) -> int:
        return self.score_cap

    def get_negative_score_cap(self) -> int:
        return self.negative_score_cap

    def get_successful_benign_points(self) -> int:
        return self.successful_benign_points

    def get_failed_benign_points(self) -> int:
        return self.failed_benign_points

    def get_successful_malicious_points(self) -> int:
        return self.successful_malicious_points

    def get_failed_malicious_points(self) -> int:
        return self.failed_malicious_points

    def get_down_points(self) -> int:
        return self.down_points

    def is_use_gunicorn(self) -> bool:
        return self.use_gunicorn

    def get_address_host(self) -> str:
        return self.address_host

    def get_address_port(self) -> int:
        return self.address_port

    def get_tls_cert(self) -> str:
        return self.tls_cert_file

    def get_tls_key(self) -> str:
        return self.tls_key_file

    def get_verify_signatures(self) -> bool:
        return self.verify_signatures
    
    def get_verify_server(self) -> bool:
        return self.verify_server

    def set_gunicorn(self, use_gunicorn: bool) -> None:
        self.use_gunicorn = use_gunicorn

    def set_address(self, address: str) -> None:
        if ":" in address:
            pieces = address.split(":")
            self.address_host = pieces[0]
            port_str = pieces[1]
        else:
            self.address_host = DEFAULT_HOST
            port_str = address

        try:
            self.address_port = int(port_str)
        except ValueError:
            fatal_error("Invalid port number: '{}'".format(port_str))

    def set_tls_cert(self, tls_cert_file: str) -> None:
        if not self.get_verify_server():
            self.tls_cert_file = None
            return
        if Path(tls_cert_file).exists():
            self.tls_cert_file = tls_cert_file
        else:
            filename = self.get_base_folder() / tls_cert_file
            if filename.exists():
                self.tls_cert_file = str(filename)
            else:
                fatal_error("File not found: '{}'".format(tls_cert_file))

    def set_tls_key(self, tls_key_file: str) -> None:
        if not self.get_verify_server():
            self.tls_key_file = None
            return
        if Path(tls_key_file).exists():
            self.tls_key_file = tls_key_file
        else:
            filename = self.get_base_folder() / tls_key_file
            if filename.exists():
                self.tls_key_file = str(filename)
            else:
                fatal_error("File not found: '{}'".format(tls_key_file))

    def remaining_time(self) -> str:
        """ Remaining competition time. """
        return time_diff(self.get_end_time())

    def time_until_start(self) -> str:
        """ Time until start. """
        return time_diff(self.start_time)

    def event_started(self) -> bool:
        """ Has event started? """
        return datetime.now(timezone.utc) >= self.get_start_time()

    def event_finished(self) -> bool:
        """ Has event finished? """
        return datetime.now(timezone.utc) >= self.get_end_time()

    """
    def load_init_config(self, filename: Path) -> None:
        # Load configuration. 
        
        if self.get_server_config_file().exists():
            answer = input("This overwrite existing configuration. "
                           "Proceed? (Y/N): ")
            if answer.lower() != "y":
                print("Aborting...")
                quit()
        
        self.parse_config(filename)

        self.store_config()

        self.export_bot_bootstrap_config()
    """

    def load_config(self, config_file: str, services_file: str) -> None:
        self.load_main_config(config_file)
        self.load_teams_config()
        self.load_services_config(services_file)
        self.load_keys_config()

    def load_main_config(self, config_file: str) -> None:

        if config_file is DEFAULT_CONFIG_FILE:
            filename = self.get_base_folder() / DEFAULT_CONFIG_FILE
        else:
            filename = config_file

        print("Initializing server from config file '{}'".format(filename))

        try:
            f = open(filename, "r")
            config = yaml.safe_load(f)
        except Exception as e:
            fatal_error("Error loading config file '{}'".format(filename), e)

        try:
            verify_schema(SERVER_CONFIG_SCHEMA, config)
        except Exception as e:
            fatal_error("Error validating config file '{}'".format(filename), e)

        # Calculate timestamps and ticks
        self.start_time = datetime.fromisoformat(config["start_time"])
        self.duration = config["duration"]
        self.prep_minutes = config["prep_minutes"]

        if (self.event_finished()):
            fatal_error(
                "The competition start time is too far in the past: {}".
                format(config["start_time"]))

        self.tick_length = config["tick_length"]

        self.server = config["server"]

        if is_ip_address(self.server):
            self.verify_server = False
            print("Not verifying server TLS certificate because server address is an IP")
        else:
            self.verify_server = True

        if is_localhost(self.server):
            print("Not verifying request signatures because we are running locally")
            self.verify_signatures = False
        else:
            self.verify_signatures = True

        # Determine score caps
        self.score_cap = config["score_cap"]
        self.negative_score_cap = config["negative_score_cap"]

        # Load score point definitions
        self.successful_benign_points = config["successful_benign_points"]
        self.failed_benign_points = config["failed_benign_points"]
        self.successful_malicious_points = \
            config["successful_malicious_points"]
        self.failed_malicious_points = config["failed_malicious_points"]
        self.down_points = config["down_points"]

        # Initialize destination folder to drop the generated files into
        self.site_folder = Path(config["site_folder"])


    def load_teams_config(self) -> None:
        filename = self.get_base_folder() / TEAMS_CONFIG_FILE

        print("Loading teams config file '{}'".format(filename))

        try:
            f = open(filename, "r")
            config = yaml.safe_load(f)
        except Exception as e:
            fatal_error("Error loading config file '{}'".format(filename), e)

        try:
            verify_schema(TEAMS_CONFIG_SCHEMA, config)
        except Exception as e:
            fatal_error("Error validating config file '{}'".format(filename), e)

        # Load team configurations
        self.teams = {}
        for team in config["teams"]:
            team_obj = Team.from_struct(team, len(self.teams))
            self.teams[team_obj.get_id()] = team_obj

    def load_services_config(self, services_file: str) -> None:
        if services_file is DEFAULT_SERVICES_FILE:
            filename = self.get_base_folder() / DEFAULT_SERVICES_FILE
        else:
            filename = services_file

        print("Loading services config file '{}'".format(filename))

        try:
            f = open(filename, "r")
            config = yaml.safe_load(f)
        except Exception as e:
            fatal_error("Error loading config file '{}'".format(filename), e)

        try:
            verify_schema(SERVICES_CONFIG_SCHEMA, config)
        except Exception as e:
            fatal_error("Error validating config file '{}'".format(filename), e)

        # Load vulnerable service configurations
        self.targets = {}
        for target in config["services"]:
            target_obj = Target.from_struct(target, len(self.targets))
            self.targets[target_obj.get_id()] = target_obj

    def load_keys_config(self) -> None:
        if not self.get_verify_signatures():
            return
        
        filename = self.get_base_folder() / KEYS_CONFIG_FILE

        print("Loading signing keys from '{}'".format(filename))

        try:
            f = open(filename, "r")
            config = yaml.safe_load(f)
        except Exception as e:
            fatal_error("Error loading config file '{}'".format(filename), e)

        try:
            verify_schema(KEYS_CONFIG_SCHEMA, config)
        except Exception as e:
            fatal_error("Error validating config file '{}'".format(filename), e)

        self.server_signing_key = Security.import_key(config["key"])
        for key_rec in config["teams"]:
            self.teams[key_rec["id"]].set_signing_key(Security.import_key(key_rec["key"]))

    """
    def store_config(self) -> None:
        data_folder = self.get_data_folder()
        make_folder(data_folder)

        config: dict[str, Any] = {}
        config["key"] = Security.export_key(self.server_signing_key)

        # Calculate timestamps and ticks
        config["start_time"] = self.start_time.isoformat(" ")
        config["duration"] = self.duration
        config["prep_minutes"] = self.prep_minutes
        config["tick_length"] = self.tick_length
        config["server"] = self.server

        # Determine score caps
        config["score_cap"] = self.score_cap
        config["negative_score_cap"] = self.negative_score_cap

        # Save score point definitions
        config["successful_benign_points"] = self.successful_benign_points
        config["failed_benign_points"] = self.failed_benign_points
        config["successful_malicious_points"] = \
            self.successful_malicious_points
        config["failed_malicious_points"] = self.failed_malicious_points
        config["down_points"] = self.down_points

        # Initialize destination folder to drop the generated files into
        config["site_folder"] = str(self.site_folder)

        # Load team configurations
        config["teams"] = []

        for team_id in self.get_team_ids():
            config["teams"].append(self.get_team(team_id).to_struct())

        # Load vulnerable service configurations
        config["services"] = []
        for target_id in self.get_target_ids():
            config["services"].append(self.get_target(target_id).to_struct())

        json_string = json.dumps(config, indent=2)

        filename = self.get_server_config_file()

        # Validate scoreboard configuration
        try:
            verify_schema(SERVER_CONFIG_SCHEMA, config)
        except Exception as e:
            fatal_error("Error validating config file '{}'".format(filename),
                        e)

        # Validate config file schema

        open(filename, "w").write(json_string)
    """

    def get_bot_config(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        result["start_time"] = self.start_time.isoformat(" ")
        result["end_time"] = self.get_end_time().isoformat(" ")
        result["tick_length"] = self.tick_length
        result["services"] = []
        for target_id in self.get_target_ids():
            result["services"].append(self.get_target(target_id).to_struct())
        return result

    """
    def export_bot_bootstrap_config(self) -> None:

        bot_config_folder = self.get_bot_config_folder()
        make_folder(bot_config_folder)
        clear_folder(bot_config_folder)

        print("Generating bot configuration files in '{}'".
              format(bot_config_folder))
        for team in self.teams.values():
            # Generate config file for every bot
            bot_config: dict[str, Any] = {}
            bot_config["id"] = team.get_id()
            bot_config["server"] = self.server
            bot_config["key"] = Security.export_key(team.get_signing_key())
            bot_config["server_key"] = Security.export_pub_key(
                self.server_signing_key)
            json_string = json.dumps(bot_config, indent=2)

            filename = Path(bot_config_folder) / BOT_CONFIG_FILE_NAME.format(
                team.get_id())

            # Validate bot configuration
            try:
                verify_schema(BOT_CONFIG_SCHEMA, bot_config)
            except Exception as e:
                fatal_error("Error validating config file '{}'".
                            format(filename), e)

            open(filename, "w").write(json_string)
    """

    def clear_data(self) -> None:
        clear_folder(self.get_data_folder())
        #clear_folder(self.get_bot_config_folder())
