#!/usr/bin/python3
# -*- coding: utf8 -*-
#
# Siege Competition Framework
#
# Author: Dmitriy Beryoza (0xd13a)

import json
from typing import Any
from typing_extensions import Self
from siege.core.attack_result import AttackResult


class AttackRecord:
    request_id: int
    result: AttackResult

    def __init__(self, request_id: int, result: AttackResult) -> None:
        self.request_id = request_id
        self.result = result

    def get_request_id(self) -> int:
        return self.request_id

    def get_result(self) -> AttackResult:
        return self.result


class TickResults:
    team_id: int
    tick: int
    results: dict[int, list[AttackRecord]]

    def __init__(self, team_id: int, tick: int) -> None:
        self.team_id = team_id
        self.tick = tick
        self.results = {}

    def record(self, target_id: int, request_id: int,
               result: AttackResult) -> None:
        # Python dictionaries are already thread safe, so this operation is
        # safe without an added lock
        # Also by current design all operations for the same traget will
        # happen in the same thread, so checking the dictionary in this case
        # and updating it is safe
        if target_id not in self.results:
            self.results[target_id] = []

        self.results[target_id].append(AttackRecord(request_id, result))

    def get_team_id(self) -> int:
        return self.team_id

    def get_tick(self) -> int:
        return self.tick

    def get_target_results(self, target_id: int) -> list[AttackRecord]:
        return self.results[target_id]

    def get_results(self) -> dict[int, list[AttackRecord]]:
        return self.results

    def to_dict(self) -> dict[str, Any]:
        doc: dict[str, Any] = {}
        doc["team_id"] = self.team_id
        doc["tick"] = self.tick
        doc["results"] = {}
        for target_id in sorted(self.results.keys()):
            doc["results"][target_id] = []
            target_results = self.get_target_results(target_id)
            for rec in target_results:
                doc["results"][target_id].append([rec.get_request_id(),
                                                  rec.get_result().value])

        return doc

    def __str__(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, doc: dict[str, Any] | Any) -> Self:
        results = cls(doc["team_id"], doc["tick"])

        for target_id in sorted(doc["results"].keys()):
            for rec in doc["results"][target_id]:
                results.record(int(target_id), rec[0], AttackResult(rec[1]))

        return results

    @classmethod
    def from_str(cls, val: str) -> Self:
        doc = json.loads(val)
        return cls.from_dict(doc)
