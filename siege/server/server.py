#!/usr/bin/python3
# -*- coding: utf8 -*-
#
# Siege Competition Framework
#
# Author: Dmitriy Beryoza (0xd13a)


import json
import traceback
from flask import Flask, make_response, request, abort
from flask.typing import ResponseReturnValue
import gunicorn.app.base  # type: ignore[import-untyped]
import queue
import time
from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore[import-untyped] # noqa: E501
from siege.core.log import log, log_error
from siege.core.tick_results import TickResults
from siege.core.util import fatal_error
from siege.server.server_config import ServerConfig
from siege.core.schemas import (COMMAND_REQUEST_SCHEMA, RESULT_SCHEMA,
                                verify_schema)
from siege.server.scoreboard import Scoreboard
from siege.core.security import Security

# Competition status banners
NOT_STARTED = "Competition has not yet started. It starts in {}."
FINISHED = "Competition has finished."
RUNNING = "Competition is running. It finishes in {}."

# Number of seconds to sleep between scoreboard generations
SLEEP_TIME = 10

app = Flask(__name__, template_folder=".")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024
app.config["EXPLAIN_TEMPLATE_LOADING"] = True


class GunicornApp(gunicorn.app.base.BaseApplication):

    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {key: value for key, value in self.options.items()
                  if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


class Server:
    config: ServerConfig
    scoreboard: Scoreboard
    result_queue: queue.Queue = queue.Queue()    # Queued submitted results

    def __init__(self, config: ServerConfig) -> None:
        self.config = config
        self.scoreboard = Scoreboard(config)

    def get_config(self) -> ServerConfig:
        return self.config

    def queue_result(self, result: TickResults) -> None:
        self.result_queue.put(result)

    def scoreboard_gen_loop(self) -> None:
        """ Scoreboard generation loop. """

        self.scoreboard.set_up()

        while True:

            # Drain the queue
            has_results = True
            while has_results:
                try:
                    result = self.result_queue.get_nowait()
                    # Process result
                    self.scoreboard.consume_result(result)

                    self.result_queue.task_done()
                except queue.Empty:
                    has_results = False

            # Select appropriate banner
            if not self.config.event_started():
                banner = NOT_STARTED.format(self.config.time_until_start())
            elif self.config.event_finished():
                banner = FINISHED
            else:
                banner = RUNNING.format(self.config.remaining_time())

            # Generate appropriate pages
            self.scoreboard.generate_files(banner)

            if self.config.event_finished():
                log("Event finished")
                break

            time.sleep(SLEEP_TIME)

        # Generate last page version
        self.scoreboard.generate_files(FINISHED)

    def run(self) -> None:
        def gen_loop():
            self.scoreboard_gen_loop()

        scheduler = BackgroundScheduler()
        scheduler.add_job(func=gen_loop, trigger="date")
        scheduler.start()

        if self.config.is_use_gunicorn():
            if self.config.get_tls_cert() is None \
                   or self.config.get_tls_key() is None:
                fatal_error("In order to run with Gunicorn supply "
                            "certificate and private key")
            options = {
                "bind": "{}:{}:".format(self.config.get_address_host(),
                                        self.config.get_address_port()),
                "workers": 1,
                "certfile": self.config.get_tls_cert(),
                "keyfile": self.config.get_tls_key()
            }
            GunicornApp(app, options).run()
        else:
            context: str | tuple[str, str] = "adhoc"
            if self.config.get_tls_cert() is None \
                    or self.config.get_tls_key() is None:
                print("Using self-signed TLS certificate")
            else:
                context = (self.config.get_tls_cert(),
                           self.config.get_tls_key())

            app.run(host=self.config.get_address_host(),
                    port=self.config.get_address_port(),
                    threaded=True, ssl_context=context)


server: Server


def get_server_instance(config: ServerConfig | None = None) -> Server:
    global server

    if config is not None:
        server = Server(config)

    return server


@app.route("/command/<int:team_id>", methods=["POST"])
def command(team_id: int) -> ResponseReturnValue:

    try:
        server = get_server_instance()

        config = server.get_config()

        if team_id not in config.get_team_ids():
            log_error("Unknown team ID {}".format(team_id),
                      request.remote_addr)
            abort(400)

        team = config.get_team(team_id)

        req = request.json
        if not isinstance(req, dict):
            log_error("Request is not a dictionary", request.remote_addr)
            abort(400)

        if config.get_verify_signatures():
            # Get verification key
            key = team.get_signing_key().publickey()

            # Get signature
            signature = request.headers.get("Signature", None)
            if signature is None:
                log_error("No signature specified for team {}".format(team_id),
                          request.remote_addr)
                abort(400)

            if not Security.verify_signature(json.dumps(req, sort_keys=True),
                                             signature, key):
                log_error("Failed signature verification for team {}".
                          format(team_id), request.remote_addr)
                abort(400)


        # Validate schema
        try:
            verify_schema(COMMAND_REQUEST_SCHEMA, req)
        except Exception as e:
            log_error("JSON doesn't match schema: {}".format(str(e)),
                      request.remote_addr)
            abort(400)

        result = {}
        if req["request"] == "ping":
            log("Received ping from team {}".
                format(team_id), request.remote_addr)
        elif req["request"] == "get_config":
            result["config"] = config.get_bot_config()
        else:
            log_error("Unsupported request type: '{}', team {}".
                      format(req["request"], team_id), request.remote_addr)
            abort(400)

        response = make_response(result)
        if config.get_verify_signatures():
            response.headers["Signature"] = Security.sign(
                json.dumps(result, sort_keys=True), config.get_key())
        return response

    except Exception:
        log_error("Error processing request: {}".
                  format(traceback.format_exc()), request.remote_addr)
        abort(400)

    return ""


@app.route("/results/<int:team_id>", methods=["POST"])
def results(team_id: int) -> ResponseReturnValue:
    """ Consume results from bot. """

    try:
        server = get_server_instance()

        config = server.get_config()

        # Make sure team exists
        if team_id not in config.get_team_ids():
            log_error("Invalid team {}".format(team_id), request.remote_addr)
            abort(404)

        team = config.get_team(team_id)

        # Get verification key
        key = team.get_signing_key().publickey()

        # Get signature
        signature = request.headers.get("Signature", None)
        if signature is None:
            log_error("No signature specified for team {}".format(team_id),
                      request.remote_addr)
            abort(400)

        if not Security.verify_signature(
                json.dumps(request.json, sort_keys=True), signature, key):
            log_error("Failed signature verification for team {}".
                      format(team_id), request.remote_addr)
            abort(400)

        # Validate schema
        try:
            verify_schema(RESULT_SCHEMA, request.json)
        except Exception as e:
            log_error("JSON doesn't match schema: {}".format(str(e)),
                      request.remote_addr)
            abort(400)

        result = TickResults.from_dict(request.json)

        tick = result.get_tick()

        # Make sure tick is in valid range
        if (tick < 0) or (tick >= config.get_total_ticks()):
            log_error("Invalid tick value {}".format(tick),
                      request.remote_addr)
            abort(400)

        # Make sure number of requests is right
        if len(result.get_results()) != len(config.get_target_ids()):
            log_error("Invalid number of targets {}".format(result),
                      request.remote_addr)
            abort(400)

        records = result.get_results()

        # Make sure number of requests is right
        for target_id in records.keys():
            target = config.get_target(target_id)

            if len(records[target_id]) != target.get_req_per_tick():
                log_error("Unexpected result number {} for target {} : {}".
                          format(len(records[target_id]), target_id, result),
                          request.remote_addr)
                abort(400)

            for attack_record in records[target_id]:
                id = attack_record.get_request_id()
                if ((id > 0 and id > target.get_vulns()) or
                        (id < 0 and id < -target.get_vulns()) or
                        id == 0):
                    log_error("Unexpected result ID {} : {}".
                              format(str(id), result), request.remote_addr)
                    abort(400)

        log("[team {}, tick {}] Received results: {}".
            format(team_id, tick, result), request.remote_addr)

        # Queue results for processing
        server.queue_result(result)

        response_payload: dict = {}
        response = make_response(response_payload)
        response.headers["Signature"] = Security.sign(
            json.dumps(response_payload, sort_keys=True), config.get_key())
        return response

    except Exception:
        log_error("Error processing request: {}".
                  format(traceback.format_exc()), request.remote_addr)
        abort(400)

    return ""
