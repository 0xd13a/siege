#!/usr/bin/python3
# -*- coding: utf8 -*-
#
# Siege Competition Framework
#
# Author: Dmitriy Beryoza (0xd13a)

from abc import ABC, abstractmethod

from siege.core.attack_result import AttackResult

"""

Attacker objects are executed by the bot to send benign and malicious requests
to the vulnerable service.

Tips for defining attacker functionality:

* Every "request" can be implemented as one or more HTTP request/response
pairs, or a terminal application conversation
* Make sure you handle any exceptions and return only one of RESULT_SUCCESS,
RESULT_DOWN, RESULT_FAILURE
* Make sure any communications you send do not hang, fail them under short
timeout
* Make sure any requests take a short time, a few seconds max
* Try to vary request contents every time, so that building a filter become
more difficult
* Try to avoid callbacks from the vulnerable service - they are easy to block
with a firewall
* Try to send non-trivial exploits, simple exploits can be easily blocked with
a WAF
* The "id" parameter is the type of vulnerability being exploited. THis means
that if you have 3 vulnerabilities defined in your code and have configured
things properly, you will receive calls for benign and malicious requests with
IDs 1, 2, and 3. We send request IDs in the same order for all teams for the
same tick.
* Do not re-seed the random number generator in order not to break up request
combination predictability

"""


"""

To build an attacker class define it like so:

    from attacker_template import Attacker

    class MyAttacker(Attacker):

        def benign_request(self, id, tick, sequence_no):
            # "id" is the vulnerability number

            # do work...
            return status # one of RESULT_SUCCESS, RESULT_DOWN, RESULT_FAILURE

        def malicious_request(self, id, tick, sequence_no):
            # "id" is the vulnerability number

            # do work...
            return status # one of RESULT_SUCCESS, RESULT_DOWN, RESULT_FAILURE

The parent class is initialized with service host and port, which are
accessible through self.host and self.port.

"""


class Attacker(ABC):

    host: str
    port: int

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port

    def get_name(self) -> str:
        return type(self).__name__

    @abstractmethod
    def benign_request(self, id: int, tick: int, sequence_no: int)\
            -> AttackResult:
        pass

    @abstractmethod
    def malicious_request(self, id: int, tick: int, sequence_no: int)\
            -> AttackResult:
        pass
