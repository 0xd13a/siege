#!/usr/bin/python3
# -*- coding: utf8 -*-
#
# Siege Competition Framework
#
# Author: Dmitriy Beryoza (0xd13a)

from pathlib import Path
import sys
import random
import traceback
from siege.core.attack_result import AttackResult
from siege.core.log import init_logging
from siege.core.util import fatal_error, load_class


def format_result(res: AttackResult) -> str:
    if res not in [AttackResult.RESULT_DOWN, AttackResult.RESULT_SUCCESS,
                   AttackResult.RESULT_FAILURE]:
        return "\033[0;31mINVALID RESULT ({})\033[0;0m".format(res)
    if res == AttackResult.RESULT_DOWN:
        return "\033[0;33mDOWN (0)\033[0;0m"
    elif res == AttackResult.RESULT_SUCCESS:
        return "\033[0;32mSUCCESS (1)\033[0;0m"
    else:
        return "\033[0;31mFAILURE (-1)\033[0;0m"


if len(sys.argv) not in [6, 7]:
    print("Usage: {} folder file class ip:port requests [tick]".format(sys.argv[0]))
    print("For example: {} foldername filename.py AttackerClassName "
          "127.0.0.1:10000 1,2,3,-1,-2,-3 10".format(sys.argv[0]))
    quit()

init_logging()

cls = load_class(sys.argv[1], sys.argv[2], sys.argv[3])
(host, port) = sys.argv[4].split(":")
try:
    cls_instance = cls(host, int(port))
except Exception as e:
    fatal_error("Could not locate class " + sys.argv[3], e)

request_types = []
for id in sys.argv[5].split(","):
    request_types.append(int(id))

tick = 0
if len(sys.argv) == 7:
    tick = int(sys.argv[6])

random.shuffle(request_types)

for i in range(len(request_types)):
    r = request_types[i]
    if r > 0:
        res = None
        try:
            res = cls_instance.benign_request(r, tick, i)
        except BaseException as e:
            print(e)
            try:
                traceback.print_exc()
            except BaseException:
                pass
            res = AttackResult.RESULT_DOWN
        print("*** BENIGN REQ {} {}".format(r, format_result(res)))
    else:
        res = None
        try:
            res = cls_instance.malicious_request(-r, tick, i)
        except BaseException as e:
            print(e)
            try:
                traceback.print_exc()
            except BaseException:
                pass
            res = AttackResult.RESULT_DOWN
        print("*** MALICIOUS REQ {} {}".format(-r, format_result(res)))
