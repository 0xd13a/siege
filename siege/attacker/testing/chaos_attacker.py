#!/usr/bin/python3
# -*- coding: utf8 -*-
#
# Siege Competition Framework
#
# Author: Dmitriy Beryoza (0xd13a)


import time
import random
from datetime import datetime
from siege.attacker.attacker import Attacker
from siege.core.attack_result import AttackResult

random.seed(datetime.now().timestamp())

SUCCESS = "success"
FAILURE = "failure"
DOWN = "down"
RANDOM = "random"
ERROR = "error"
BADERROR = "baderror"
DELAY = "delay"


class ChaosAttacker(Attacker):

    def benign_request(self, id: int, tick: int, sequence_no: int) -> AttackResult:
        if self.host == SUCCESS:
            return AttackResult.RESULT_SUCCESS
        if self.host == FAILURE:
            return AttackResult.RESULT_FAILURE
        if self.host == DOWN:
            return AttackResult.RESULT_DOWN
        if self.host == RANDOM:
            return random.choice([AttackResult.RESULT_SUCCESS,
                                  AttackResult.RESULT_FAILURE,
                                  AttackResult.RESULT_DOWN])
        if self.host == ERROR:
            raise BaseException("exception")
        if self.host == BADERROR:
            _ = 1 / 0
        if self.host == DELAY:
            time.sleep(self.port)
            return AttackResult.RESULT_SUCCESS
        raise Exception("Unknown request type '{}'".format(self.host))

    def malicious_request(self, id: int, tick: int, sequence_no: int) -> AttackResult:
        return self.benign_request(id, tick, sequence_no)
