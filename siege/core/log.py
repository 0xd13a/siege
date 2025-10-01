#!/usr/bin/python3
# -*- coding: utf8 -*-
#
# Siege Competition Framework
#
# Author: Dmitriy Beryoza (0xd13a)

from datetime import datetime
import logging
from pathlib import Path
from typing import Any

from siege.core.util import clear_folder

log_folder: Path
output_to_console: bool = False
logger: logging.Logger


def init_logging(folder: Path | None = None, file: str | None = None) -> None:
    global log_folder, logger, output_to_console

    if folder is None or file is None:
        output_to_console = True
        return

    log_folder = folder
    logger = logging.getLogger(__name__)
    logging.basicConfig(filename=folder / file, encoding="utf-8",
                        level=logging.ERROR, format="%(message)s")


def clear_logs() -> None:
    global log_folder
    clear_folder(log_folder)


def get_prefix() -> str:
    """ Create a message prefix with timestamp. """
    return "[{}]".format(datetime.now().strftime("%H:%M:%S"))


def log(msg: Any, ip: str | None = None) -> None:
    """ Format a message and send it to output. """
    output_log_message("[*] {}{} {}".
                       format(get_prefix(),
                              " ["+ip+"]" if ip is not None else "", str(msg)))


def log_error(msg: Any, ip: str | None = None) -> None:
    """ Format an error message and send it to output. """
    output_log_message("[-] {}{} {}".
                       format(get_prefix(),
                              " ["+ip+"]" if ip is not None else "", str(msg)))


def output_log_message(message: str) -> None:
    global logger
    if output_to_console:
        print(message, flush=True)
    else:
        logger.error(message)
