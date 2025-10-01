#!/usr/bin/python3
# -*- coding: utf8 -*-
#
# Siege Competition Framework
#
# Author: Dmitriy Beryoza (0xd13a)

# Execution results:

from enum import Enum


class AttackResult(Enum):
    RESULT_SUCCESS: int = 1
    RESULT_DOWN: int = 0
    RESULT_FAILURE: int = -1
