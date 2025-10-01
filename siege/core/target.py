#!/usr/bin/python3
# -*- coding: utf8 -*-
#
# Siege Competition Framework
#
# Author: Dmitriy Beryoza (0xd13a)

from typing import Any


class Target:
    id: int
    name: str
    folder: str
    file: str
    cls: str
    address: str
    description: str
    vulns: int
    req_per_tick: int
    schedule: dict[int, list[int]]

    def __init__(self, id: int, name: str, folder: str, file: str, cls: str, address: str,
                 description: str, vulns: int, req_per_tick: int) -> None:
        self.id = id
        self.name = name
        self.folder = folder
        self.file = file
        self.cls = cls
        self.address = address
        self.description = description
        self.vulns = vulns
        self.req_per_tick = req_per_tick
        self.schedule = {}

    @staticmethod
    def from_struct(struct: dict[str, Any], id: int | None = None):
        if id is None:
            id = struct["id"]
        target_obj = Target(id, struct["name"], struct["folder"],
                            struct["file"],
                            struct["class"], struct["address"],
                            struct["description"], struct["vulns"],
                            struct["requests"]["per_tick"])

        schedule = struct["requests"]["schedule"]
        for element in schedule:
            target_obj.add_schedule(element["tick"], element["set"])
        return target_obj

    def to_struct(self) -> dict[str, Any]:
        target_struct: dict[str, Any] = {}
        target_struct["id"] = self.get_id()
        target_struct["name"] = self.get_name()
        target_struct["folder"] = self.get_folder()
        target_struct["file"] = self.get_file()
        target_struct["class"] = self.get_class()
        target_struct["address"] = self.get_address()
        target_struct["description"] = self.get_description()
        target_struct["vulns"] = self.get_vulns()
        target_struct["requests"] = {}
        target_struct["requests"]["per_tick"] = self.get_req_per_tick()
        schedule = self.get_schedule()
        target_struct["requests"]["schedule"] = []
        for tick in schedule:
            sched_item: dict[str, Any] = {}
            sched_item["tick"] = tick
            sched_item["set"] = schedule[tick]
            target_struct["requests"]["schedule"].append(sched_item)
        return target_struct

    def get_id(self) -> int:
        return self.id

    def get_name(self) -> str:
        return self.name

    def get_folder(self) -> str:
        return self.folder

    def get_file(self) -> str:
        return self.file

    def get_class(self) -> str:
        return self.cls

    def get_address(self) -> str:
        return self.address

    def get_description(self) -> str:
        return self.description

    def get_vulns(self) -> int:
        return self.vulns

    def get_req_per_tick(self) -> int:
        return self.req_per_tick

    def get_schedule(self) -> dict[int, list[int]]:
        return self.schedule

    def add_schedule(self, tick: int, reqs: list[int]) -> None:
        self.schedule[tick] = reqs
