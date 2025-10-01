#!/usr/bin/python3
# -*- coding: utf8 -*-
#
# Siege Competition Framework
#
# Author: Dmitriy Beryoza (0xd13a)

import json
from pathlib import Path
import jsonschema
from typing import Any
from siege.core.util import fatal_error

# Document schema
SERVER_CONFIG_SCHEMA = "server-config-schema.json"
BOT_CONFIG_SCHEMA = "bot-config-schema.json"
RESULT_SCHEMA = "result-schema.json"
COMMAND_REQUEST_SCHEMA = "command-request-schema.json"
COMMAND_RESPONSE_SCHEMA = "command-response-schema.json"
SERVICES_CONFIG_SCHEMA = "services-config-schema.json"
SERVICES_LIGHT_CONFIG_SCHEMA = "services-light-config-schema.json"
TEAMS_CONFIG_SCHEMA = "teams-config-schema.json"
KEYS_CONFIG_SCHEMA = "keys-config-schema.json"

SCHEMAS_FOLDER = Path(__file__).resolve().parent.parent / "schemas/"

loaded_schemas: dict[str, Any] = {}

known_schemas = [SERVER_CONFIG_SCHEMA, BOT_CONFIG_SCHEMA, RESULT_SCHEMA,
                 COMMAND_REQUEST_SCHEMA, COMMAND_RESPONSE_SCHEMA, 
                 SERVICES_CONFIG_SCHEMA, SERVICES_LIGHT_CONFIG_SCHEMA,
                 TEAMS_CONFIG_SCHEMA, KEYS_CONFIG_SCHEMA]


def verify_schema(name: str, doc: dict[str, Any] | Any) -> None:
    if len(loaded_schemas) == 0:
        for schema_name in known_schemas:
            schema_file = SCHEMAS_FOLDER / schema_name
            try:
                f = open(schema_file)
                schema = json.load(f)
            except Exception as e:
                fatal_error("Error loading schema file '{}'".
                            format(schema_file), e)
            loaded_schemas[schema_name] = schema

    schema_to_verify = loaded_schemas[name]

    # Validate the document
    jsonschema.validate(instance=doc, schema=schema_to_verify)
