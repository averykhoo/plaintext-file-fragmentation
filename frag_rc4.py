from typing import List
from typing import Union


def rc4(key: Union[str, bytes, bytearray],
        input_bytes: Union[bytes, bytearray],
        initialization_vector: Union[bytes, bytearray] = b'',
        ) -> bytearray:
    """
    single-function RC4-drop stream encryption
    uses IV to determine how much of keystream to skip
    e.g. to mimic RC4-drop-768, set IV to b'\xFE\x02'

    :param key: 1 to 256 bytes (remainder will be ignored)
    :param input_bytes: data to encrypt / decrypt
    :param initialization_vector: 1 to 16 bytes (remainder will be ignored)
    :return: encoded bytes
    """
    if not isinstance(key, (str, bytes, bytearray)):
        raise TypeError('key should be bytes')
    if not isinstance(input_bytes, (bytes, bytearray)):
        raise TypeError('input should be bytes')
    if not isinstance(initialization_vector, (bytes, bytearray)):
        raise TypeError('IV should be bytes')
    assert len(key) > 0

    # convert to bytes (kind of)
    if isinstance(key, str):
        key = [ord(char) for char in key[:256]]
    key_length = len(key)

    # generate S-box
    j = 0
    s: List[int] = list(range(256))
    for i in range(256):
        j = (j + s[i] + key[i % key_length]) & 0xFF
        s[i], s[j] = s[j], s[i]

    # init variables
    i = 0
    j = 0

    # skip N bytes using the IV
    if initialization_vector:
        skip = (510 + sum(c << i for i, c in enumerate(initialization_vector[:16]))) & 0xFFFF

        for _ in range(skip):
            i = (i + 1) & 0xFF
            j = (j + s[i]) & 0xFF
            s[i], s[j] = s[j], s[i]

    # don't destroy the input bytes
    if isinstance(input_bytes, bytes):
        output_bytes = bytearray(input_bytes)  # bytes are immutable
    else:
        output_bytes = input_bytes[:]  # shallow copy

    # in-place xor with key stream
    for idx in range(len(output_bytes)):
        i += 1
        i &= 0xFF
        j += s[i]
        j &= 0xFF
        s[i], s[j] = s[j], s[i]

        output_bytes[idx] ^= s[(s[i] + s[j]) & 0xFF]

    return output_bytes
