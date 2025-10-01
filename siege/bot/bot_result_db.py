#!/usr/bin/python3
# -*- coding: utf8 -*-
#
# Siege Competition Framework
#
# Author: Dmitriy Beryoza (0xd13a)

from pathlib import Path
from typing import Any

from siege.core.db import ResultDB
from siege.core.tick_results import TickResults


class BotResultDB(ResultDB):

    def __init__(self, db_name: Path) -> None:
        super().__init__(db_name)

        if not self.database_name.exists():
            self.exec_sql("CREATE TABLE results (tick INT, results "
                          "VARCHAR(2000) NOT NULL, sent INT);", [], True)

    def save_result(self, tick: int, result: TickResults) -> None:
        """ Save result to database. """
        self.exec_sql("INSERT INTO results (tick, results, sent) "
                      "VALUES(?, ?, ?);", [tick, str(result), 0], True)

    def mark_tick_result_sent(self, tick: int) -> None:
        self.exec_sql("UPDATE results SET sent = 1 WHERE tick = ?;", [tick],
                      True)

    def load_unsent_results(self) -> list[Any]:
        return self.exec_sql("SELECT tick, results FROM results WHERE "
                             "sent = 0;", [])
