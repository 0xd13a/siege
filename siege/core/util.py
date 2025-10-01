#!/usr/bin/python3
# -*- coding: utf8 -*-
#
# Siege Competition Framework
#
# Author: Dmitriy Beryoza (0xd13a)

from datetime import datetime, timezone
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import shutil
from typing import Any
import ipaddress
from urllib.parse import urlparse
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def to_millis(dt: datetime) -> int:
    """ Convert timestamp to milliseconds. """
    return int(dt.timestamp()*1000)


def time_diff(point: datetime) -> str:
    """ Calculate human-readable time difference. """
    difference = point - datetime.now(timezone.utc)
    return "{} hour(s) {} minute(s)".format(
        int(difference.total_seconds() // 3600),
        int(difference.total_seconds() // 60) % 60)


def fatal_error(msg: str, e: Exception | None = None) -> None:
    print(msg)
    if e is not None:
        print(e)
    quit()


def make_folder(folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)


def clear_folder(folder: Path, recursive: bool = False) -> None:
    for filename in folder.iterdir():
        try:
            if filename.is_file() or filename.is_symlink():
                filename.unlink()
            elif filename.is_dir() and recursive:
                shutil.rmtree(filename)
        except Exception as e:
            print("Failed to delete %s. Reason: %s" % (filename, e))


def load_class(folder: str, file:str, cls: str) -> Any:
    
    # TODO: resolve error handling

    module_path = Path("services") / folder / "attacker" / file
    
    spec = spec_from_file_location("", module_path)
    if spec is None:
        return None
    custom_module = module_from_spec(spec)
    if spec.loader is None:
        return None
    spec.loader.exec_module(custom_module)
    cls = getattr(custom_module, cls)
    return cls


def get_sorted_values(data: dict[Any, Any]) -> list[Any]:
    keys = sorted(data.keys())
    result = []
    for key in keys:
        result.append(data[key])
    return result

def is_ip_address(url: str):
    parsed_url = urlparse(url)
    try:
        ipaddress.ip_address(str(parsed_url.hostname))
        return True
    except ValueError:
        return False

def is_localhost(url: str):
    parsed_url = urlparse(url)

    if str(parsed_url.hostname).lower() in ["127.0.0.1", "localhost", "::1"]:
        return True
    return False
