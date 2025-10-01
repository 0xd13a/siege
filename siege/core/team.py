#!/usr/bin/python3
# -*- coding: utf8 -*-
#
# Siege Competition Framework
#
# Author: Dmitriy Beryoza (0xd13a)

from typing import Any
from Crypto.PublicKey import RSA

from siege.core.security import Security


class Team:
    id: int
    name: str
    email: str
    bot_signing_key: RSA.RsaKey

    def __init__(self, id: int, name: str, email: str | None,
                 bot_signing_key: RSA.RsaKey | None = None) -> None:
        self.id = id
        self.name = name
        self.email = email
        self.bot_signing_key = bot_signing_key

    @staticmethod
    def from_struct(struct: dict[str, Any], id: int | None = None):
        if id is None:
            return Team(struct["id"], struct["name"], struct["email"],
                        Security.import_key(struct["key"]))
        else:
            return Team(id, struct["name"], struct["email"])

    def to_struct(self) -> dict[str, Any]:
        team_struct: dict[str, Any] = {}
        team_struct["id"] = self.get_id()
        team_struct["name"] = self.get_name()
        team_struct["email"] = self.get_email()
        if self.key is not None:
            team_struct["key"] = Security.export_key(self.get_signing_key())
        return team_struct

    def get_id(self) -> int:
        return self.id

    def get_name(self) -> str:
        return self.name

    def get_signing_key(self) -> RSA.RsaKey:
        return self.bot_signing_key
    
    def get_email(self) -> str:
        return self.email

    def set_signing_key(self, bot_signing_key: RSA.RsaKey) -> None:
        self.bot_signing_key = bot_signing_key
