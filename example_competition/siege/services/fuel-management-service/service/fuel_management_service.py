#!/usr/bin/python3
# -*- coding: utf8 -*-
#
# Can-doo Nuclear Generating Station
#
# Fuel Management Service
#
# Created by PowerGPT.
#

# Only authorized users with a correct username and password are allowed in.
#
# Users can be of 2 types: Monitors and Management Technicians. Monitors are
# only allowed to see the current state of the fuel in the reactor, while
# Management Technicians can also order fuel loading and unloading.
#
# Fuel in Can-doo reactor is stored in the form of 'bundles' that are put into
# 'channels'. Not all channels need to be filled. Used bundles are candidates
# for removal.
#
# Fuel management has to follow these rules:
#
# - You cannot fill more than 70% of the slots, or the reactor will become
# unstable
# - You cannot fill less than 20% of the slots, or the reactor will lack
# necessary fuel and will have to undergo an emergency shutdown
# - You cannot remove more bundles than there are candidates for removal, or
# good fuel will be wasted

from flask import (Flask, render_template, redirect, request, abort,
                   make_response)
import sqlite3
import jwt
import sys
import base64
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature.pkcs1_15 import PKCS115_SigScheme


DB = "./fms-users.db"

pub_key = "-----BEGIN PUBLIC KEY-----\nMIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQ"\
    "DFGtmtCW3HTi4fYq/rWsbc4pMP\n3+r0Amy3Egscv8y2TgW0MWVQXYwB79GC03yeuFPPI5gJ"\
    "4LxAp/cDCAYA0OOZI+SV\nuyYGCD4FGY7H+s2V3WASjSdraBBSIXIIQ42UyOPwLhtjvjsT0p"\
    "mLqoTlthwIPL++\nrhTNDy/BeOkAj4mlbQIDAQAB\n-----END PUBLIC KEY-----"

jwt_key = "Pz6gNPWUsb2evdibVtYkptOVMptR1rN2aqisIoIgWkYQZSF8Z11PBwRukvus"


NUMBER_OF_CHANNELS_IN_REACTOR = 400
bundles_used = 0
bundles_candidates_for_removal = 0


# Set up port to communicate on
server_port = 10001
if len(sys.argv) == 2:
    server_port = int(sys.argv[1])

app = Flask(__name__, template_folder=".")


# User informaton record
class User:
    user = ""

    def __init__(self, user):
        self.user = user

    def get_username(self):
        return self.user


def get_user(request):
    """ Retrieve currently logged in user. """

    token = request.cookies.get('token')
    if token is None:
        return User(None)
    else:
        try:
            decoded_data = jwt.decode(jwt=token, key=jwt_key,
                                      algorithms=["HS256"])
        except Exception:
            return User(None)
        return User(decoded_data["user"])


def set_current_user(response, user):
    """ Set currently logged in user. """

    if user is None:
        response.delete_cookie('token')
    else:
        token = jwt.encode(payload={"user": user.get_username()}, key=jwt_key,
                           algorithm="HS256")
        response.set_cookie('token', token)


@app.route("/sensor", methods=['POST'])
def sensor():
    """ Reactor inventory sensor will call this API to inform it of the
    currently loaded reactor bundles """
    global bundles_used, bundles_candidates_for_removal

    # Get signature
    signature = request.headers.get('Signature', None)

    if signature is None:
        abort(400)

    try:
        signature = base64.b64decode(signature)
    except Exception:
        abort(400)

    # Verify the signature to make sure the inventory sensor is truly sending
    # this request
    hash = SHA256.new(request.get_data())
    verifier = PKCS115_SigScheme(RSA.import_key(pub_key))
    try:
        verifier.verify(hash, signature)
    except Exception:
        abort(400)

    # Update status with values from the sensor
    bundles_used = int(request.form.get('bundles_used'))
    bundles_candidates_for_removal = int(
        request.form.get('bundles_candidates_for_removal'))

    return ""


@app.route("/status", methods=['GET'])
def status():
    """ Display current reactor fuel status. """

    user = get_user(request)

    if user.get_username() is None:
        return redirect("/login")

    resp = make_response(render_template(
        "status_template.html", username=user.get_username(),
        used_channels=bundles_used,
        ready_bundles=bundles_candidates_for_removal))
    set_current_user(resp, user)
    return resp


@app.route("/change", methods=['POST'])
def change():
    """ Specify number of bundles to insert into the reactor, and/or to
    remove. """
    global bundles_used, bundles_candidates_for_removal

    user = get_user(request)
    if user.get_username() is None:
        return redirect("/login")

    # TODO: at some point we will have to implement some checks, but for now
    # Management Technicians know how to move bundles around correctly

    bundles_to_insert = 0
    try:
        bundles_to_insert = int(request.form.get('bundles_to_insert'))
    except Exception:
        pass

    bundles_to_remove = 0
    try:
        bundles_to_remove = int(request.form.get('bundles_to_remove'))
    except Exception:
        pass

    bundles_used += bundles_to_insert
    bundles_used -= bundles_to_remove
    bundles_candidates_for_removal -= bundles_to_remove

    resp = make_response(redirect("/status"))
    set_current_user(resp, user)
    return resp


@app.route("/", methods=['GET'])
def root():
    """ Site entry point. """
    return redirect("/login")


@app.route("/login", methods=['GET', 'POST'])
def login():
    """ Main login handler. """
    user = get_user(request)

    if user.get_username() is None:
        if request.method == 'GET':
            return render_template("login_template.html")

        # Check input parameters
        username = request.form.get('username')
        pwd = request.form.get('password')
        if username is None or pwd is None or pwd == "":
            return "<html><body><h2>Invalid login!</h2></body></html>", 401

        # Load user from database
        rows = []
        con = sqlite3.connect(DB)
        cur = con.cursor()
        for row in cur.execute("select user from users where user=?",
                               (username,)):
            rows.append([row[0]])
        cur.close()
        con.close()

        if len(rows) >= 1:
            val = rows[0]
            current_user = User(val[0])
            resp = make_response(redirect("/status"))
            set_current_user(resp, current_user)
            return resp
        else:
            return "<html><body><h2>Error logging in user</h2></body></html>",
        401
    else:
        resp = make_response(redirect("/login"))
        set_current_user(resp, None)
        return resp


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=server_port, ssl_context='adhoc')
