#!/usr/bin/python3
# -*- coding: utf8 -*-
#
# Siege Competition Framework
#
# Author: Dmitriy Beryoza (0xd13a)

from pathlib import Path
import sqlite3
import traceback
from typing import Any

from siege.core.log import log_error


class ResultDB:

    # Database name
    database_name: Path

    def __init__(self, db_name: Path) -> None:
        self.database_name = db_name

    def exec_sql(self, query: str, param=list[Any],
                 update: bool = False) -> list[Any]:
        """ Execute SQL query with error handling. """
        con = None
        cur = None
        rows = []
        try:
            con = sqlite3.connect(self.database_name)
            cur = con.cursor()
            for row in cur.execute(query, param):
                rows.append(row)
            # If it's a query that changes database - commit results
            if update:
                con.commit()
        except Exception:
            log_error("Error executing query: {}".
                      format(traceback.format_exc()))
        finally:
            if cur is not None:
                cur.close()
            if con is not None:
                con.close()
        return rows
