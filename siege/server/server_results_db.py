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


class ServerResultDB(ResultDB):

    def __init__(self, db_name: Path) -> None:
        super().__init__(db_name)

        if not self.database_name.exists():
            self.exec_sql(
                "CREATE TABLE results (results VARCHAR(2000) NOT NULL);", [],
                True)

    def load_database(self) -> list[Any]:
        """ Load or create database. """
        rows = self.exec_sql("SELECT * FROM results;", [])

        return rows

    def save_score(self, result: TickResults) -> None:
        """ Save score to database. """
        self.exec_sql("INSERT INTO results (results) VALUES (?);",
                      [str(result)], True)
