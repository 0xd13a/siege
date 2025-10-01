#!/usr/bin/python3
# -*- coding: utf8 -*-
#
# Siege Competition Framework
#
# Author: Dmitriy Beryoza (0xd13a)

import argparse
from pathlib import Path

from siege.bot.bot import Bot
from siege.bot.bot_config import BotConfig
from siege.core.log import clear_logs, init_logging

DEFAULT_BASE_FOLDER = "."


def main() -> None:

    print("Siege Attack Bot\n")

    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--base-folder", metavar="BASE_FOLDER",
                        dest="base_folder_arg", default=DEFAULT_BASE_FOLDER,
                        help="Base folder for all files and data, default "
                        "- '{}'".format(DEFAULT_BASE_FOLDER))
    parser.add_argument("config", nargs="?", const="", metavar="CONFIG_FILE",
                        help="Initialize server from config file, default "
                        "- 'config/bot-config-*.yaml'")
    parser.add_argument("-r", "--reset", dest="reset_arg", action="store_true",
                        help="Clear collected results and log files")

    args = parser.parse_args()

    bot_config = BotConfig()
    bot_config.set_base_folder(Path(args.base_folder_arg))
    print("Using base folder: {}\n".format(args.base_folder_arg))

    bot_config.load_initial_config(args.config)

    init_logging(bot_config.get_log_folder(), "bot-{}.log".
                 format(bot_config.get_team_id()))

    if args.reset_arg:
        print("Clearing generated logs and data...")
        bot_config.clear_results()
        clear_logs()
        quit()

    bot = Bot(bot_config)
    bot.run()


if __name__ == "__main__":
    main()
