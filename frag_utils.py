import hashlib
import math
import os
import struct
import warnings
from pathlib import PurePath
from typing import List
from typing import Union


def format_bytes(num_bytes):
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


def format_seconds(num_seconds):
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


def hash_file(file_path: Union[PurePath, os.PathLike], hash_func: str = 'SHA1'):
    hash_func = hash_func.strip().lower()
    assert hash_func in ['md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512']
    hash_obj = getattr(hashlib, hash_func)()
    fd = os.open(str(file_path), (os.O_RDONLY | os.O_BINARY))  # the O_BINARY flag is windows-only
    for block in iter(lambda: os.read(fd, 65536), b''):  # 2**16 is a multiple of the hash block size
        hash_obj.update(block)
    os.close(fd)
    return hash_obj.hexdigest().upper()


def hash_content(content: Union[bytes, bytearray], hash_func: str = 'SHA1'):
    hash_func = hash_func.strip().lower()
    assert hash_func in ['md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512']
    hash_obj = getattr(hashlib, hash_func)()
    hash_obj.update(content)
    return hash_obj.hexdigest().upper()


def password_to_bytes(password_string: str,
                      salt: Union[bytes, bytearray] = b'sodium--chloride' * 32,
                      length: int = 512) -> bytes:
    assert isinstance(password_string, str)
    assert 1 <= length < 1024 * 1024

    if len(salt) < length:
        # https://crackstation.net/hashing-security.htm#salt
        warnings.warn(f'salt too short, should be as long as your output ({length} bytes)')

    password_length = 0
    password_chunks: List[bytes] = []

    while password_length < length:
        chunk = hashlib.sha3_512(salt + bytes(str(password_length), 'ascii') + password_string.encode('utf8')).digest()
        password_length += len(chunk)
        password_chunks.append(chunk)

    return b''.join(password_chunks)[:length]


_a85chars = [b'!', b'"', b'#', b'$', b'%', b'&', b"'", b'(', b')', b'*', b'+', b',', b'-', b'.', b'/', b'0', b'1',
             b'2', b'3', b'4', b'5', b'6', b'7', b'8', b'9', b':', b';', b'<', b'=', b'>', b'?', b'@', b'A', b'B',
             b'C', b'D', b'E', b'F', b'G', b'H', b'I', b'J', b'K', b'L', b'M', b'N', b'O', b'P', b'Q', b'R', b'S',
             b'T', b'U', b'V', b'W', b'X', b'Y', b'Z', b'[', b'\\', b']', b'^', b'_', b'`', b'a', b'b', b'c', b'd',
             b'e', b'f', b'g', b'h', b'i', b'j', b'k', b'l', b'm', b'n', b'o', b'p', b'q', b'r', b's', b't', b'u']
_a85chars2 = [(a + b) for a in _a85chars for b in _a85chars]
_A85START = b"<~"
_A85END = b"~>"


def _to_bytes(s, encoding='ascii'):
    if hasattr(s, 'encode'):
        try:
            return s.encode(encoding)
        except UnicodeEncodeError:
            if encoding == 'ascii':
                raise ValueError('string argument should contain only ASCII characters')
            raise
    if isinstance(s, (bytes, bytearray)):
        return s
    try:
        return memoryview(s).tobytes()
    except TypeError:
        raise TypeError('argument should be a bytes-like object or ASCII string, not {}'.format(s.__class__.__name__))


def _85encode(b, chars, chars2, pad=False, foldnuls=False, foldspaces=False):
    # Helper function for a85encode and b85encode
    if not isinstance(b, (bytes, bytearray)):
        b = memoryview(b).tobytes()

    padding = (-len(b)) % 4
    if padding:
        b = b + b'\0' * padding
    words = struct.Struct('!%dI' % (len(b) // 4)).unpack(b)

    chunks = [b'z' if foldnuls and not word else
              b'y' if foldspaces and word == 0x20202020 else
              (chars2[word // 614125] +
               chars2[word // 85 % 7225] +
               chars[word % 85])
              for word in words]

    if padding and not pad:
        if chunks[-1] == b'z':
            chunks[-1] = chars[0] * 5
        chunks[-1] = chunks[-1][:-padding]

    return b''.join(chunks)


def a85encode(b, foldspaces=False, wrapcol=0, pad=False, adobe=False):
    """Encode bytes-like object b using Ascii85 and return a bytes object.

    foldspaces is an optional flag that uses the special short sequence 'y'
    instead of 4 consecutive spaces (ASCII 0x20) as supported by 'btoa'. This
    feature is not supported by the "standard" Adobe encoding.

    wrapcol controls whether the output should have newline (b'\\n') characters
    added to it. If this is non-zero, each output line will be at most this
    many characters long.

    pad controls whether the input is padded to a multiple of 4 before
    encoding. Note that the btoa implementation always pads.

    adobe controls whether the encoded byte sequence is framed with <~ and ~>,
    which is used by the Adobe implementation.
    """

    result = _85encode(b, _a85chars, _a85chars2, pad, True, foldspaces)

    if adobe:
        result = _A85START + result
    if wrapcol:
        wrapcol = max(2 if adobe else 1, wrapcol)
        chunks = [result[i: i + wrapcol]
                  for i in range(0, len(result), wrapcol)]
        if adobe:
            if len(chunks[-1]) + 2 > wrapcol:
                chunks.append(b'')
        result = b'\n'.join(chunks)
    if adobe:
        result += _A85END

    return result


def a85decode(b, foldspaces=False, adobe=False, ignorechars=b' \t\n\r\v'):
    """Decode the Ascii85 encoded bytes-like object or ASCII string b.

    foldspaces is a flag that specifies whether the 'y' short sequence should be
    accepted as shorthand for 4 consecutive spaces (ASCII 0x20). This feature is
    not supported by the "standard" Adobe encoding.

    adobe controls whether the input sequence is in Adobe Ascii85 format (i.e.
    is framed with <~ and ~>).

    ignorechars should be a byte string containing characters to ignore from the
    input. This should only contain whitespace characters, and by default
    contains all whitespace characters in ASCII.

    The result is returned as a bytes object.
    """
    b = _to_bytes(b)
    if adobe:
        if not b.endswith(_A85END):
            raise ValueError('Ascii85 encoded byte sequences must end with {}'.format(repr(_A85END))
                             )
        if b.startswith(_A85START):
            b = b[2:-2]  # Strip off start/end markers
        else:
            b = b[:-2]

    # We have to go through this stepwise, so as to ignore spaces and handle special short sequences
    pack_i = struct.Struct('!I').pack
    decoded = []
    decoded_append = decoded.append
    curr = []

    for x in b + b'u' * 4:
        if b'!'[0] <= x <= b'u'[0]:
            if type(x) is str:
                x = ord(x)
            curr.append(x)
            if len(curr) == 5:
                acc = 0
                for y in curr:
                    acc = 85 * acc + (y - 33)
                try:
                    decoded_append(pack_i(acc))
                except struct.error:
                    raise ValueError('Ascii85 overflow')
                # curr_clear()
                del curr
                curr = []
        elif x == b'z'[0]:
            if curr:
                raise ValueError('z inside Ascii85 5-tuple')
            decoded_append(b'\0\0\0\0')
        elif foldspaces and x == b'y'[0]:
            if curr:
                raise ValueError('y inside Ascii85 5-tuple')
            decoded_append(b'\x20\x20\x20\x20')
        elif x in ignorechars:
            # Skip whitespace
            continue
        else:
            raise ValueError('Non-Ascii85 digit found: {}'.format(repr(x)))

    result = b''.join(decoded)
    padding = 4 - len(curr)
    if padding:
        # Throw away the extra padding
        result = result[:-padding]
    return result
