import hashlib
import hmac
import math
import os
import warnings
from pathlib import PurePath
from typing import Union

PEPPER = b'''Lr>=9ObAWplJB^>#g<QAK$,<+O'bK;UU:Eim%3S01WZdV4_5g-6Mao_EOS>3W,V7''' + \
         b'''?Wqm[#)[Tn52B8s-&I1N'E[C3Q[pB2(FnJ/8rEGQ1OEojE!&L**HH.$EqChdhJUZ''' + \
         b'''a"Ki]5P+M/4>'-F7dXX&M7qJ^GI7r3pt/2&_&uULVL=PZ3*?Mdir`5YZbrW`4hIJ''' + \
         b''''8P%!7I)1Pq6[CEog'C<(>kP:*52D!@-%I#`Ztj*dki19Ck(n(_Ca4O8URVGEr0@''' + \
         b'''hHZ"2ZY$qJ;I2Ta^Jm1^eq3Br$A6btq=OmQAA7ip?aa<N6K1J;<dl1h&5Q"6j-TE''' + \
         b'''B77#$jb'*STXgiSq"7^"O5;RL7aHpoNOW$0hSaoZLhq<M/)k:=Z,S",8CY(i?964''' + \
         b'''S]-[[dCI@8n)ntRdXY*WB]_.qLJVF_sQUIlR'Eb2%9`]:Mfi%aRjF=R9*`kmm>M5''' + \
         b'''"40&=a.CaR.S&IRbkQMDl32!l97:`G)Y/4nn$&KBK?A/`YKD),QOYUVhmE6OQ'rI''' + \
         b'''?^IioYnmp=_so!_k>X!Y/HI&()9$DWQ/%8ghW.3"*FOPfX:7?@?gDBrli]1Q,Ks4''' + \
         b'''Bd28;*f3-"UdUS<r8L-<LCO*M=f_pHp7Z7[R&e^,e1DnD4=s'X4C3_OuW1e'Wba]''' + \
         b'''YtfljY&:CfD.E`q)^s4^E$?a>qhcZW`d6]n)KhHQjLQFFAYuFGl%Ios.oQbJoEBa''' + \
         b'''##Qh"?1FBV3gMEE<Ce`T/]QEjqZ)'N'A6!=(.>b^>3T-jjli+(QC?42@FmVAG)%<'''  # 768 almost-random bytes


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


def key_derivation_function(password_string: Union[str, bytes, bytearray],
                            salt: Union[bytes, bytearray] = b'',
                            length: int = 512
                            ) -> bytes:
    assert 1 <= length <= 1024 * 1024

    # warn if salt is too short, see: https://crackstation.net/hashing-security.htm#salt
    if len(salt) < length:
        warnings.warn(f'salt too short, should be as long as your output ({length} bytes)')

    # combine pepper and password
    if isinstance(password_string, str):
        key_bytes = hmac.digest(PEPPER, password_string.encode('utf8'), digest='sha3_512')
    else:
        key_bytes = hmac.digest(PEPPER, password_string, digest='sha3_512')

    return hashlib.scrypt(key_bytes, salt=salt + PEPPER, n=16384, r=32, p=1, dklen=length, maxmem=80 * 1024 * 1024)
