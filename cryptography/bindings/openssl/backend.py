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

from __future__ import absolute_import, division, print_function

import itertools
import sys

import cffi

from cryptography.primitives import interfaces
from cryptography.primitives.block.ciphers import AES, Camellia, TripleDES
from cryptography.primitives.block.modes import CBC, CTR, ECB, OFB, CFB


class Backend(object):
    """
    OpenSSL API wrapper.
    """
    _modules = [
        "asn1",
        "bignum",
        "bio",
        "conf",
        "crypto",
        "dh",
        "dsa",
        "engine",
        "err",
        "evp",
        "hmac",
        "nid",
        "opensslv",
        "pem",
        "pkcs7",
        "pkcs12",
        "rand",
        "rsa",
        "ssl",
        "x509",
        "x509name",
        "x509v3",
    ]

    def __init__(self):
        self.ffi = cffi.FFI()
        includes = []
        functions = []
        macros = []
        for name in self._modules:
            __import__("cryptography.bindings.openssl." + name)
            module = sys.modules["cryptography.bindings.openssl." + name]
            self.ffi.cdef(module.TYPES)

            macros.append(module.MACROS)
            functions.append(module.FUNCTIONS)
            includes.append(module.INCLUDES)

        # loop over the functions & macros after declaring all the types
        # so we can set interdependent types in different files and still
        # have them all defined before we parse the funcs & macros
        for func in functions:
            self.ffi.cdef(func)
        for macro in macros:
            self.ffi.cdef(macro)

        # We include functions here so that if we got any of their definitions
        # wrong, the underlying C compiler will explode. In C you are allowed
        # to re-declare a function if it has the same signature. That is:
        #   int foo(int);
        #   int foo(int);
        # is legal, but the following will fail to compile:
        #   int foo(int);
        #   int foo(short);
        self.lib = self.ffi.verify(
            source="\n".join(includes + functions),
            libraries=["crypto", "ssl"],
        )

        self.lib.OpenSSL_add_all_algorithms()
        self.lib.SSL_load_error_strings()

        self.ciphers = Ciphers(self.ffi, self.lib)
        self.hashes = Hashes(self.ffi, self.lib)

    def openssl_version_text(self):
        """
        Friendly string name of linked OpenSSL.

        Example: OpenSSL 1.0.1e 11 Feb 2013
        """
        return self.ffi.string(self.lib.OPENSSL_VERSION_TEXT).decode("ascii")


class GetCipherByName(object):
    def __init__(self, fmt):
        self._fmt = fmt

    def __call__(self, backend, cipher, mode):
        cipher_name = self._fmt.format(cipher=cipher, mode=mode).lower()
        return backend.lib.EVP_get_cipherbyname(cipher_name.encode("ascii"))


class Ciphers(object):
    def __init__(self, ffi, lib):
        super(Ciphers, self).__init__()
        self.ffi = ffi
        self.lib = lib
        self._cipher_registry = {}
        self._register_default_ciphers()

    def supported(self, cipher, mode):
        try:
            adapter = self._cipher_registry[type(cipher), type(mode)]
        except KeyError:
            return False
        evp_cipher = adapter(self, cipher, mode)
        return self.ffi.NULL != evp_cipher

    def register_cipher_adapter(self, cipher_cls, mode_cls, adapter):
        if (cipher_cls, mode_cls) in self._cipher_registry:
            raise ValueError("Duplicate registration for: {0} {1}".format(
                cipher_cls, mode_cls)
            )
        self._cipher_registry[cipher_cls, mode_cls] = adapter

    def _register_default_ciphers(self):
        for cipher_cls, mode_cls in itertools.product(
            [AES, Camellia],
            [CBC, CTR, ECB, OFB, CFB],
        ):
            self.register_cipher_adapter(
                cipher_cls,
                mode_cls,
                GetCipherByName("{cipher.name}-{cipher.key_size}-{mode.name}")
            )
        for mode_cls in [CBC, CFB, OFB]:
            self.register_cipher_adapter(
                TripleDES,
                mode_cls,
                GetCipherByName("des-ede3-{mode.name}")
            )

    def create_encrypt_ctx(self, cipher, mode):
        ctx, evp, iv_nonce = self._create_ctx(cipher, mode)
        res = self.lib.EVP_EncryptInit_ex(ctx, evp, self.ffi.NULL, cipher.key,
                                          iv_nonce)
        assert res != 0
        # We purposely disable padding here as it's handled higher up in the
        # API.
        self.lib.EVP_CIPHER_CTX_set_padding(ctx, 0)
        return ctx

    def create_decrypt_ctx(self, cipher, mode):
        ctx, evp, iv_nonce = self._create_ctx(cipher, mode)
        res = self.lib.EVP_DecryptInit_ex(ctx, evp, self.ffi.NULL, cipher.key,
                                          iv_nonce)
        assert res != 0
        # We purposely disable padding here as it's handled higher up in the
        # API.
        self.lib.EVP_CIPHER_CTX_set_padding(ctx, 0)
        return ctx

    def _create_ctx(self, cipher, mode):
        ctx = self.lib.EVP_CIPHER_CTX_new()
        ctx = self.ffi.gc(ctx, self.lib.EVP_CIPHER_CTX_free)
        evp_cipher = self._cipher_registry[type(cipher), type(mode)](
            self, cipher, mode
        )
        assert evp_cipher != self.ffi.NULL
        if isinstance(mode, interfaces.ModeWithInitializationVector):
            iv_nonce = mode.initialization_vector
        elif isinstance(mode, interfaces.ModeWithNonce):
            iv_nonce = mode.nonce
        else:
            iv_nonce = self.ffi.NULL

        return (ctx, evp_cipher, iv_nonce)

    def update_encrypt_ctx(self, ctx, data):
        block_size = self.lib.EVP_CIPHER_CTX_block_size(ctx)
        buf = self.ffi.new("unsigned char[]", len(data) + block_size - 1)
        outlen = self.ffi.new("int *")
        res = self.lib.EVP_EncryptUpdate(ctx, buf, outlen, data, len(data))
        assert res != 0
        return self.ffi.buffer(buf)[:outlen[0]]

    def update_decrypt_ctx(self, ctx, data):
        block_size = self.lib.EVP_CIPHER_CTX_block_size(ctx)
        buf = self.ffi.new("unsigned char[]", len(data) + block_size - 1)
        outlen = self.ffi.new("int *")
        res = self.lib.EVP_DecryptUpdate(ctx, buf, outlen, data, len(data))
        assert res != 0
        return self.ffi.buffer(buf)[:outlen[0]]

    def finalize_encrypt_ctx(self, ctx):
        block_size = self.lib.EVP_CIPHER_CTX_block_size(ctx)
        buf = self.ffi.new("unsigned char[]", block_size)
        outlen = self.ffi.new("int *")
        res = self.lib.EVP_EncryptFinal_ex(ctx, buf, outlen)
        assert res != 0
        res = self.lib.EVP_CIPHER_CTX_cleanup(ctx)
        assert res == 1
        return self.ffi.buffer(buf)[:outlen[0]]

    def finalize_decrypt_ctx(self, ctx):
        block_size = self.lib.EVP_CIPHER_CTX_block_size(ctx)
        buf = self.ffi.new("unsigned char[]", block_size)
        outlen = self.ffi.new("int *")
        res = self.lib.EVP_DecryptFinal_ex(ctx, buf, outlen)
        assert res != 0
        res = self.lib.EVP_CIPHER_CTX_cleanup(ctx)
        assert res == 1
        return self.ffi.buffer(buf)[:outlen[0]]


class Hashes(object):
    def __init__(self, ffi, lib):
        super(Hashes, self).__init__()
        self.ffi = ffi
        self.lib = lib

    def supported(self, hash_cls):
        return (self.ffi.NULL !=
                self.lib.EVP_get_digestbyname(hash_cls.name.encode("ascii")))

    def create_ctx(self, hashobject):
        ctx = self.lib.EVP_MD_CTX_create()
        ctx = self.ffi.gc(ctx, self.lib.EVP_MD_CTX_destroy)
        evp_md = self.lib.EVP_get_digestbyname(hashobject.name.encode("ascii"))
        assert evp_md != self.ffi.NULL
        res = self.lib.EVP_DigestInit_ex(ctx, evp_md, self.ffi.NULL)
        assert res != 0
        return ctx

    def update_ctx(self, ctx, data):
        res = self.lib.EVP_DigestUpdate(ctx, data, len(data))
        assert res != 0

    def finalize_ctx(self, ctx, digest_size):
        buf = self.ffi.new("unsigned char[]", digest_size)
        res = self.lib.EVP_DigestFinal_ex(ctx, buf, self.ffi.NULL)
        assert res != 0
        res = self.lib.EVP_MD_CTX_cleanup(ctx)
        assert res == 1
        return self.ffi.buffer(buf)[:digest_size]

    def copy_ctx(self, ctx):
        copied_ctx = self.lib.EVP_MD_CTX_create()
        copied_ctx = self.ffi.gc(copied_ctx, self.lib.EVP_MD_CTX_destroy)
        res = self.lib.EVP_MD_CTX_copy_ex(copied_ctx, ctx)
        assert res != 0
        return copied_ctx


backend = Backend()
