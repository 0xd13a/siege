#!/usr/bin/python3
# -*- coding: utf8 -*-
#
# Siege Competition Framework
#
# Author: Dmitriy Beryoza (0xd13a)

import argparse
from pathlib import Path

from siege.core.log import clear_logs, init_logging
from siege.server.server_config import (DEFAULT_ADDRESS, DEFAULT_CONFIG_FILE,
                                        DEFAULT_SERVICES_FILE, ServerConfig)
from siege.server.server import get_server_instance

DEFAULT_BASE_FOLDER = "."


def main() -> None:

    print("Siege Competition Server\n")

    parser = argparse.ArgumentParser()
    #parser.add_argument("-i", "--init", nargs="?", const="",
    #                    metavar="CONFIG_FILE", dest="init_arg",
    #                    help="Initialize server from config file, "
    #                    "default - '{}'".format(DEFAULT_CONFIG_FILE))
    parser.add_argument("-c", "--config-file", metavar="CONFIG_FILE",
                        dest="config_file_arg", default=DEFAULT_CONFIG_FILE,
                        help="Config file for general server settings, "
                        "default - '{}'".format(DEFAULT_CONFIG_FILE))
    parser.add_argument("-s", "--services-file", metavar="SERVICES_FILE",
                        dest="services_file_arg", default=DEFAULT_SERVICES_FILE,
                        help="Config file with vulnerable service settings, "
                        "default - '{}'".format(DEFAULT_SERVICES_FILE))
    parser.add_argument("-r", "--reset", dest="reset_arg",
                        action="store_true",
                        help="Clear collected results and log files")
    parser.add_argument("-b", "--base-folder", metavar="BASE_FOLDER",
                        dest="base_folder_arg", default=DEFAULT_BASE_FOLDER,
                        help="Base folder for all files and data, "
                        "default - '{}'".format(DEFAULT_BASE_FOLDER))
    parser.add_argument("--cert", metavar="CERT_FILE", dest="cert_arg",
                        help="Certificate file")
    parser.add_argument("--key", metavar="KEY_FILE", dest="key_arg",
                        help="Private key file")
    parser.add_argument("-a", "--address", metavar="ADDRESS",
                        dest="address_arg", default=DEFAULT_ADDRESS,
                        help="Address and port (or just the port) to bind the"
                        " server to, default - '{}'".format(DEFAULT_ADDRESS))
    # TODO: disabling Gunicorn support until we can work out a stable way to
    # exhange data
    # parser.add_argument("-g", "--gunicorn", dest="gunicorn_arg",
    # action="store_true", default=False, help="Use Gunicorn to run server")

    args = parser.parse_args()

    server_config = ServerConfig()
    server_config.set_base_folder(Path(args.base_folder_arg))
    print("Using base folder: {}\n".format(args.base_folder_arg))

    init_logging(server_config.get_log_folder(), "server.log")

    if args.reset_arg:
        print("Clearing generated logs and data...")
        server_config.clear_data()
        clear_logs()
        quit()

    """
    if args.init_arg is not None:
        if len(args.init_arg) == 0:
            config_file = server_config.get_base_folder() / DEFAULT_CONFIG_FILE
        else:
            config_file = args.init_arg

        print("Initializing server from config file '{}'".format(config_file))

        server_config.load_init_config(config_file)
        quit()
    """

    server_config.set_gunicorn(False)  # args.gunicorn_arg)
    server_config.set_address(args.address_arg)
    server_config.set_tls_cert(args.cert_arg)
    server_config.set_tls_key(args.key_arg)

    server_config.load_config(args.config_file, args.service_file_arg)
    server = get_server_instance(server_config)
    server.run()


if __name__ == "__main__":
    main()
