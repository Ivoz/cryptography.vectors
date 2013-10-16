# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test using the NIST Test Vectors
"""

from __future__ import absolute_import, division, print_function

import binascii

from cryptography.primitives.block import ciphers, modes

from .utils import generate_encrypt_test
from ..utils import load_nist_vectors_from_file


class TestAES_CBC(object):
    test_KAT = generate_encrypt_test(
        lambda path: load_nist_vectors_from_file(path, "ENCRYPT"),
        "AES",
        "KAT",
        [
            "CBCGFSbox128.rsp",
            "CBCGFSbox192.rsp",
            "CBCGFSbox256.rsp",
            "CBCKeySbox128.rsp",
            "CBCKeySbox192.rsp",
            "CBCKeySbox256.rsp",
            "CBCVarKey128.rsp",
            "CBCVarKey192.rsp",
            "CBCVarKey256.rsp",
            "CBCVarTxt128.rsp",
            "CBCVarTxt192.rsp",
            "CBCVarTxt256.rsp",
        ],
        lambda key, iv: ciphers.AES(binascii.unhexlify(key)),
        lambda key, iv: modes.CBC(binascii.unhexlify(iv)),
    )

    test_MMT = generate_encrypt_test(
        lambda path: load_nist_vectors_from_file(path, "ENCRYPT"),
        "AES",
        "MMT",
        [
            "CBCMMT128.rsp",
            "CBCMMT192.rsp",
            "CBCMMT256.rsp",
        ],
        lambda key, iv: ciphers.AES(binascii.unhexlify(key)),
        lambda key, iv: modes.CBC(binascii.unhexlify(iv)),
    )


class TestAES_ECB(object):
    test_KAT = generate_encrypt_test(
        lambda path: load_nist_vectors_from_file(path, "ENCRYPT"),
        "AES",
        "KAT",
        [
            "ECBGFSbox128.rsp",
            "ECBGFSbox192.rsp",
            "ECBGFSbox256.rsp",
            "ECBKeySbox128.rsp",
            "ECBKeySbox192.rsp",
            "ECBKeySbox256.rsp",
            "ECBVarKey128.rsp",
            "ECBVarKey192.rsp",
            "ECBVarKey256.rsp",
            "ECBVarTxt128.rsp",
            "ECBVarTxt192.rsp",
            "ECBVarTxt256.rsp",
        ],
        lambda key: ciphers.AES(binascii.unhexlify(key)),
        lambda key: modes.ECB(),
    )

    test_MMT = generate_encrypt_test(
        lambda path: load_nist_vectors_from_file(path, "ENCRYPT"),
        "AES",
        "MMT",
        [
            "ECBMMT128.rsp",
            "ECBMMT192.rsp",
            "ECBMMT256.rsp",
        ],
        lambda key: ciphers.AES(binascii.unhexlify(key)),
        lambda key: modes.ECB(),
    )


class TestAES_OFB(object):
    test_KAT = generate_encrypt_test(
        lambda path: load_nist_vectors_from_file(path, "ENCRYPT"),
        "AES",
        "KAT",
        [
            "OFBGFSbox128.rsp",
            "OFBGFSbox192.rsp",
            "OFBGFSbox256.rsp",
            "OFBKeySbox128.rsp",
            "OFBKeySbox192.rsp",
            "OFBKeySbox256.rsp",
            "OFBVarKey128.rsp",
            "OFBVarKey192.rsp",
            "OFBVarKey256.rsp",
            "OFBVarTxt128.rsp",
            "OFBVarTxt192.rsp",
            "OFBVarTxt256.rsp",
        ],
        lambda key, iv: ciphers.AES(binascii.unhexlify(key)),
        lambda key, iv: modes.OFB(binascii.unhexlify(iv)),
    )

    test_MMT = generate_encrypt_test(
        lambda path: load_nist_vectors_from_file(path, "ENCRYPT"),
        "AES",
        "MMT",
        [
            "OFBMMT128.rsp",
            "OFBMMT192.rsp",
            "OFBMMT256.rsp",
        ],
        lambda key, iv: ciphers.AES(binascii.unhexlify(key)),
        lambda key, iv: modes.OFB(binascii.unhexlify(iv)),
    )


class TestAES_CFB(object):
    test_KAT = generate_encrypt_test(
        lambda path: load_nist_vectors_from_file(path, "ENCRYPT"),
        "AES",
        "KAT",
        [
            "CFB128GFSbox128.rsp",
            "CFB128GFSbox192.rsp",
            "CFB128GFSbox256.rsp",
            "CFB128KeySbox128.rsp",
            "CFB128KeySbox192.rsp",
            "CFB128KeySbox256.rsp",
            "CFB128VarKey128.rsp",
            "CFB128VarKey192.rsp",
            "CFB128VarKey256.rsp",
            "CFB128VarTxt128.rsp",
            "CFB128VarTxt192.rsp",
            "CFB128VarTxt256.rsp",
        ],
        lambda key, iv: ciphers.AES(binascii.unhexlify(key)),
        lambda key, iv: modes.CFB(binascii.unhexlify(iv)),
    )


    test_MMT = generate_encrypt_test(
        lambda path: load_nist_vectors_from_file(path, "ENCRYPT"),
        "AES",
        "MMT",
        [
            "CFB128MMT128.rsp",
            "CFB128MMT192.rsp",
            "CFB128MMT256.rsp",
        ],
        lambda key, iv: ciphers.AES(binascii.unhexlify(key)),
        lambda key, iv: modes.CFB(binascii.unhexlify(iv)),
    )
