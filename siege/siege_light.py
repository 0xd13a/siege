#!/usr/bin/python3
# -*- coding: utf8 -*-
#
# Siege Competition Framework
#
# Author: Dmitriy Beryoza (0xd13a)

# Attacker Portal

from siege.core.schemas import (SERVICES_LIGHT_CONFIG_SCHEMA, verify_schema)
from flask import Flask, render_template, redirect, request, abort, make_response
import sys
import traceback
import yaml
import random
import argparse
from pathlib import Path
from siege.core.attack_result import AttackResult
from siege.attacker.attacker import Attacker
from siege.core.log import init_logging
from siege.core.util import fatal_error, load_class

TEMPLATE = "index_template.html"
STATIC_FOLDER = "static"
DEFAULT_BASE_FOLDER = "."
DEFAULT_PORT = 80
DEFAULT_SERVICES_CONFIG_FILE = "config/services.yaml"
SITE_FOLDER = "site/"

BENIGN_REQUEST = True
MALICIOUS_REQUEST = False

current_tick = 0

init_logging()

app = Flask(__name__)

attackers: list[Attacker] = []
requests: list[int] = []
flags: list[list[str]] = []

base_folder: Path

def main():
    global app, attackers, requests, flags

    print("Siege Light Portal\n")

    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--base-folder", metavar="BASE_FOLDER",
                        dest="base_folder_arg", default=DEFAULT_BASE_FOLDER,
                        help="Base folder for all files and data, default "
                        "- '{}'".format(DEFAULT_BASE_FOLDER))
    parser.add_argument("-p", "--port", metavar="PORT", dest="port_arg", 
                        default=DEFAULT_PORT, help="Port to run the portal"
                        " on, default - '{}'".format(DEFAULT_PORT))
    parser.add_argument("-s", "--services-config", metavar="CONFIG_FILE",
                        dest="services_config_arg",
                        default=DEFAULT_SERVICES_CONFIG_FILE,
                        help="Config file for vulnerable services, default "
                        "- '{}'".format(DEFAULT_SERVICES_CONFIG_FILE))

    args = parser.parse_args()

    base_folder = Path(args.base_folder_arg)

    # Set up and parse the config file
    try:
        with open(base_folder / args.services_config_arg, 'r') as file:
            # Using safe_load for security reasons
            config = yaml.safe_load(file)
    except Exception as e:
        fatal_error(f"Error loading config file '{args.services_config_arg}'", e)

    try:
        verify_schema(SERVICES_LIGHT_CONFIG_SCHEMA, config)
    except Exception as e:
        fatal_error(f"Error validating config file '{args.services_config_arg}'", e)

    # Figure out paths
    site_folder = Path(base_folder).resolve() / SITE_FOLDER
    app.template_folder = site_folder
    app.static_folder = site_folder / STATIC_FOLDER

    for target in config["services"]:
        folder = target["folder"]
        file = target["file"]
        class_name = target["class"]
        address = target["address"]

        cls = load_class(folder, file, class_name)
        (host, port) = address.split(":")
        try:
            cls_instance = cls(host, int(port))
        except Exception as e:
            fatal_error("Could not locate class " + class_name, e)

        attackers.append(cls_instance)

        request_no = int(target["requests"])
        if request_no < 1:
            fatal_error("Number of requsts must be > 0: {request_no}")
        request_list = []
        if request_no % 2 == 1:
            request_list.append(MALICIOUS_REQUEST)
        request_list.extend([MALICIOUS_REQUEST] * (request_no // 2))
        request_list.extend([BENIGN_REQUEST] * (request_no // 2))
        requests.append(request_list)

        flags.append(target["flags"])

    app.run(host='0.0.0.0', port=args.port_arg)

@app.route("/", methods=['GET'])
def root():
    """ Site entry point. """
    return render_template(TEMPLATE)
    
@app.route("/attack/<int:service>/<int:attack_type>", methods=['GET'])
def attack(service, attack_type):
    """ Attack handler. """
    global current_tick

    if service < 0 or service >= len(attackers):
        abort(500)
    if attack_type < 0 or attack_type >= len(flags[service]):
        abort(500)

    print(f"\n*** Tesing service {service} scenario {attack_type}")

    random.shuffle(requests[service])

    req_num = len(requests[service])
    secure_reqs = 0

    current_tick += 1

    request_id = attack_type + 1

    for i in range(len(requests[service])):
        req_benign = requests[service][i]
        result = None

        if req_benign:
            print(f"*** Benign request {request_id}")
            try:
                result = attackers[service].benign_request(request_id, current_tick, i)
            except BaseException as e:
                print(e)
                try:
                    traceback.print_exc()
                except BaseException:
                    pass
                result = AttackResult.RESULT_DOWN
            print(f"*** Benign request {request_id}: {result.name}")

            if result == AttackResult.RESULT_SUCCESS:
                secure_reqs += 1
        else:
            print(f"*** Malicious request {request_id}")
            try:
                result = attackers[service].malicious_request(request_id, current_tick, i)
            except BaseException as e:
                print(e)
                try:
                    traceback.print_exc()
                except BaseException:
                    pass
                result = AttackResult.RESULT_DOWN
            print(f"*** Malicious request {request_id}: {result.name}")

            if result == AttackResult.RESULT_FAILURE:
                secure_reqs += 1

    if secure_reqs == req_num:
        print(f"*** Tesing service {service} scenario {attack_type}: attack neutralized")

        return "Congratulations, your service is now immune to this type of attack! Here is the verification code: " +\
            flags[service][attack_type]
    else:
        print(f"*** Tesing service {service} scenario {attack_type}: attack still works")
        return "The service is still vulnerable, keep trying."

if __name__ == '__main__':
    main()