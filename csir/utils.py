from datetime import datetime
from functools import lru_cache, wraps
from json import loads, dumps
from re import sub
from time import sleep


# we don't need nanosecond precision here,
# and python only supports it in 3.8+,
# so just drop the nanoseconds/microseconds, if any
def clean_timestamp(timestamp):
    return datetime.strptime(
        sub('\.\d+Z$', "Z", timestamp),
        '%Y-%m-%dT%H:%M:%SZ'
    )


def with_retries(func, tries):
    while tries > 0:
        try:
            return func()
        except:
            tries -= 1
            if tries > 0:
                sleep(0.1)
                continue
            raise


def lru_wrapper(func):
    cache = lru_cache(maxsize=None)

    def deserialise(value):
        try:
            return loads(value)
        except Exception:
            return value

    def func_with_serialized_params(*args, **kwargs):
        _args = tuple([deserialise(arg) for arg in args])
        _kwargs = {k: deserialise(v) for k, v in kwargs.items()}
        return func(*_args, **_kwargs)

    cached_function = cache(func_with_serialized_params)

    @wraps(func)
    def lru_decorator(*args, **kwargs):
        _args = tuple([dumps(arg, sort_keys=True) if type(arg) in (list, dict) else arg for arg in args])
        _kwargs = {k: dumps(v, sort_keys=True) if type(v) in (list, dict) else v for k, v in kwargs.items()}
        return cached_function(*_args, **_kwargs)

    lru_decorator.cache_info = cached_function.cache_info
    lru_decorator.cache_clear = cached_function.cache_clear
    return lru_decorator


# Copyright (c) 2017 Pieter Wuille
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""Reference implementation for Bech32 and segwit addresses."""

"""
Note:
Adjusted by Ryan Funduk (obo Figment Networks Inc.)
for Cosmos-like purposes on Feb 2, 2020
"""


__CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"


def __bech32_polymod(values):
    """Internal function that computes the Bech32 checksum."""
    generator = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3]
    chk = 1
    for value in values:
        top = chk >> 25
        chk = (chk & 0x1ffffff) << 5 ^ value
        for i in range(5):
            chk ^= generator[i] if ((top >> i) & 1) else 0
    return chk


def __bech32_hrp_expand(hrp):
    """Expand the HRP into values for checksum computation."""
    return [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]


def __bech32_verify_checksum(hrp, data):
    """Verify a checksum given HRP and converted data characters."""
    return __bech32_polymod(__bech32_hrp_expand(hrp) + data) == 1


def __bech32_create_checksum(hrp, data):
    """Compute the checksum values given HRP and data."""
    values = __bech32_hrp_expand(hrp) + data
    polymod = __bech32_polymod(values + [0, 0, 0, 0, 0, 0]) ^ 1
    return [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]


def encode_bech32(hrp, data):
    """Compute a Bech32 string given HRP and data values."""
    combined = data + __bech32_create_checksum(hrp, data)
    return hrp + '1' + ''.join([__CHARSET[d] for d in combined])


def decode_bech32(bech):
    """Validate a Bech32 string, and determine HRP and data."""
    if ((any(ord(x) < 33 or ord(x) > 126 for x in bech)) or
        (bech.lower() != bech and bech.upper() != bech)):
        return (None, None)
    bech = bech.lower()
    pos = bech.rfind('1')
    if pos < 1 or pos + 7 > len(bech) or len(bech) > 90:
        return (None, None)
    if not all(x in __CHARSET for x in bech[pos+1:]):
        return (None, None)
    hrp = bech[:pos]
    data = [__CHARSET.find(x) for x in bech[pos+1:]]
    if not __bech32_verify_checksum(hrp, data):
        return (None, None)
    return (hrp, data[:-6])
