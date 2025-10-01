#!/usr/bin/python3
# -*- coding: utf8 -*-
#
# Siege Competition Framework
#
# Author: Dmitriy Beryoza (0xd13a)

import base64
import traceback
from typing import Any
from Crypto.PublicKey import RSA
from Crypto.Signature.pkcs1_15 import PKCS115_SigScheme
from Crypto.Hash import SHA256


class Security:

    @staticmethod
    def generate_key() -> RSA.RsaKey:
        return RSA.generate(1024)

    @staticmethod
    def import_key(key: str) -> RSA.RsaKey:
        return RSA.import_key(key)

    @staticmethod
    def export_key(key: RSA.RsaKey) -> str:
        return key.export_key("PEM").decode()

    @staticmethod
    def export_pub_key(key: RSA.RsaKey) -> str:
        return key.public_key().export_key("PEM").decode()

    @staticmethod
    def verify_signature(content: Any, signature: str,
                         key: RSA.RsaKey) -> bool:

        try:
            signature_bytes = base64.b64decode(signature)
        except Exception:
            return False

        # Verify the signature
        hash = SHA256.new(str(content).encode())
        verifier = PKCS115_SigScheme(key)
        try:
            verifier.verify(hash, signature_bytes)
        except Exception:
            traceback.print_exc()
            return False

        return True

    @staticmethod
    def sign(content: Any, key: RSA.RsaKey) -> str:
        hash = SHA256.new(str(content).encode())
        signer = PKCS115_SigScheme(key)
        signature = signer.sign(hash)

        return base64.b64encode(signature).decode("utf-8")
