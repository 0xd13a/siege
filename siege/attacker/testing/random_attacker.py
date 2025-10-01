#!/usr/bin/python3
# -*- coding: utf8 -*-
#
# Siege Competition Framework
#
# Author: Dmitriy Beryoza (0xd13a)


import random
from datetime import datetime
from siege.attacker.attacker import Attacker
from siege.core.attack_result import AttackResult

random.seed(datetime.now().timestamp())


class RandomAttacker(Attacker):

    def benign_request(self, id: int, tick: int, sequence_no: int) -> AttackResult:
        result = random.randrange(10)
        if result == 4:
            return AttackResult.RESULT_DOWN
        if result > 4:
            return AttackResult.RESULT_SUCCESS
        return AttackResult.RESULT_FAILURE

    def malicious_request(self, id: int, tick: int, sequence_no: int) -> AttackResult:
        result = random.randrange(10)
        if result == 4:
            return AttackResult.RESULT_DOWN
        if result > 4:
            return AttackResult.RESULT_FAILURE
        return AttackResult.RESULT_SUCCESS
