import hashlib
import math
import os
import warnings
from pathlib import PurePath
from typing import List
from typing import Union


def format_bytes(num_bytes: Union[float, int]) -> str:
    """
    string formatting
    :type num_bytes: int
    :rtype: str
    """

    # handle negatives
    if num_bytes < 0:
        minus = '-'
    else:
        minus = ''
    num_bytes = abs(num_bytes)

    # ±1 byte (singular form)
    if num_bytes == 1:
        return f'{minus}1 Byte'

    # determine unit
    unit = 0
    while unit < 8 and num_bytes > 999:
        num_bytes /= 1024.0
        unit += 1
    unit = ['Bytes', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB'][unit]

    # exact or float
    if num_bytes % 1:
        return f'{minus}{num_bytes:,.2f} {unit}'
    else:
        return f'{minus}{num_bytes:,.0f} {unit}'


def format_seconds(num_seconds: Union[float, int]) -> str:
    """
    string formatting
    note that the days in a month is kinda fuzzy
    kind of takes leap years into account, but as a result the years are fuzzy
    :type num_seconds: int | float
    """

    # handle negatives
    if num_seconds < 0:
        minus = '-'
    else:
        minus = ''
    num_seconds = abs(num_seconds)

    # zero (not compatible with decimals below)
    if num_seconds == 0:
        return '0 seconds'

    # 1 or more seconds
    if num_seconds >= 1:
        unit = 0
        denominators = [60.0, 60.0, 24.0, 7.0, 365.25 / 84.0, 12.0]
        while unit < 6 and num_seconds > denominators[unit] * 0.9:
            num_seconds /= denominators[unit]
            unit += 1
        unit = [u'seconds', u'minutes', u'hours', u'days', u'weeks', u'months', u'years'][unit]

        # singular form
        if num_seconds == 1:
            unit = unit[:-1]

        # exact or float
        if num_seconds % 1:
            return f'{minus}{num_seconds:,.2f} {unit}'
        else:
            return f'{minus}{num_seconds:,.0f} {unit}'

    # fractions of a second (ms, μs, ns)
    else:
        unit = 0
        while unit < 3 and num_seconds < 0.9:
            num_seconds *= 1000
            unit += 1
        unit = [u'seconds', u'milliseconds', u'microseconds', u'nanoseconds'][unit]

        # singular form
        if num_seconds == 1:
            unit = unit[:-1]

        # exact or float
        if num_seconds % 1 and num_seconds > 1:
            return f'{minus}{num_seconds:,.2f} {unit}'
        elif num_seconds % 1:
            # noinspection PyStringFormat
            num_seconds = f'{{N:,.{1 - int(math.floor(math.log10(abs(num_seconds))))}f}}'.format(N=num_seconds)
            return f'{minus}{num_seconds} {unit}'
        else:
            return f'{minus}{num_seconds:,.0f} {unit}'


def hash_file(file_path: Union[PurePath, os.PathLike],
              hash_func: str = 'SHA1'
              ) -> str:
    hash_func = hash_func.strip().lower()
    assert hash_func in ['md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512']
    hash_obj = getattr(hashlib, hash_func)()
    fd = os.open(str(file_path), (os.O_RDONLY | os.O_BINARY))  # the O_BINARY flag is windows-only
    for block in iter(lambda: os.read(fd, 65536), b''):  # 2**16 is a multiple of the hash block size
        hash_obj.update(block)
    os.close(fd)
    return hash_obj.hexdigest().upper()


def hash_content(content: Union[bytes, bytearray],
                 hash_func: str = 'SHA1'
                 ) -> str:
    hash_func = hash_func.strip().lower()
    assert hash_func in ['md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512']
    hash_obj = getattr(hashlib, hash_func)()
    hash_obj.update(content)
    return hash_obj.hexdigest().upper()


def password_to_bytes(password_string: str,
                      salt: Union[bytes, bytearray] = b'sodium--chloride' * 32,
                      length: int = 512
                      ) -> bytes:
    assert isinstance(password_string, str)
    assert 1 <= length < 1024 * 1024

    if len(salt) < length:
        # https://crackstation.net/hashing-security.htm#salt
        warnings.warn(f'salt too short, should be as long as your output ({length} bytes)')

    password_length = 0
    password_chunks: List[bytes] = []

    while password_length < length:
        pepper = bytes(str(password_length), 'ascii')  # very bad pepper but meh it's RC4 anyway
        chunk = hashlib.sha3_512(password_string.encode('utf8') + pepper + salt).digest()
        password_length += len(chunk)
        password_chunks.append(chunk)

    return b''.join(password_chunks)[:length]
