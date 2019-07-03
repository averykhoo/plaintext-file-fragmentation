import codecs
from typing import List
from typing import Union


def rc4(key: Union[str, bytes, bytearray],
        input_bytes: Union[bytes, bytearray],
        initialization_vector: Union[bytes, bytearray] = b'',
        ) -> bytearray:
    """
    single-function RC4-drop stream encryption
    uses IV to determine how much of keystream to skip
    to mimic RC4-drop-768, set IV to b'\xfe\x02'

    :param key: 1 to 256 bytes
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
    S = list(range(256))
    for i in range(256):
        j = (j + S[i] + key[i % key_length]) & 0xFF
        S[i], S[j] = S[j], S[i]

    # init variables
    i = 0
    j = 0

    # skip N bytes using the IV
    if len(initialization_vector):
        skip = 510 + sum(c << i for i, c in enumerate(initialization_vector[:16])) & 0xFFFF

        for _ in range(skip):
            i = (i + 1) & 0xFF
            j = (j + S[i]) & 0xFF
            S[i], S[j] = S[j], S[i]

    # don't destroy the input bytes
    if isinstance(input_bytes, bytes):
        output_bytes = bytearray(input_bytes)  # bytes are immutable
    else:
        output_bytes = input_bytes[:]  # shallow copy

    # in-place xor with key stream
    for idx in range(len(output_bytes)):
        i += 1
        i &= 0xFF
        j += S[i]
        j &= 0xFF
        S[i], S[j] = S[j], S[i]

        output_bytes[idx] ^= S[(S[i] + S[j]) & 0xFF]

    return output_bytes


def rc4_stream(key):
    # key as numbers
    # key = [ord(char) for char in key[:256]]
    key_length = len(key)

    j = 0
    S = list(range(256))
    for i in range(256):
        j = (j + S[i] + key[i % key_length]) & 0xFF
        S[i], S[j] = S[j], S[i]

    i = 0
    j = 0
    while True:
        i = (i + 1) & 0xFF

        j = (j + S[i]) & 0xFF
        S[i], S[j] = S[j], S[i]
        yield S[(S[i] + S[j]) & 0xFF]


def rc4_encode(key, input_bytes, skip=0):
    keystream = rc4_stream(key)
    for _ in range(skip):
        next(keystream)

    input_bytes = bytearray(input_bytes)
    for i in range(len(input_bytes)):
        input_bytes[i] ^= next(keystream)

    return input_bytes


def rc4a_stream(key):
    # key as numbers
    # key = [ord(char) for char in key[:256]]
    key_length = len(key)

    j = 0
    S1 = list(range(256))  # type: List[int]
    for i in range(256):
        j = (j + S1[i] + key[i % key_length]) & 0xFF
        S1[i], S1[j] = S1[j], S1[i]

    j = 0
    S2 = list(range(256))  # type: List[int]
    for i in range(256):
        j = (j + S2[i] + key[i % key_length]) & 0xFF
        S2[i], S2[j] = S2[j], S2[i]

    i = 0
    j1 = 0
    j2 = 0
    while True:
        i = (i + 1) & 0xFF

        j1 = (j1 + S1[i]) & 0xFF
        S1[i], S1[j1] = S1[j1], S1[i]
        yield S2[(S1[i] + S1[j1]) & 0xFF]

        j2 = (j2 + S2[i]) & 0xFF
        S2[i], S2[j2] = S2[j2], S2[i]
        yield S1[(S2[i] + S2[j2]) & 0xFF]


def rc4a_encode(key, input_bytes, initialization_vector=b''):
    skip = 510 + sum(c << i for i, c in enumerate(initialization_vector)) & 0xFFFF

    keystream = rc4a_stream(key)
    for _ in range(skip):
        next(keystream)

    input_bytes = bytearray(input_bytes)
    for i in range(len(input_bytes)):
        input_bytes[i] ^= next(keystream)

    return input_bytes


class RC4(object):
    def __init__(self, key: Union[str, bytes, bytearray], skip=None):
        """
        >>> RC4('key').encode_str('test')
        [127, 9, 71, 153]
        >>> RC4('key').decode_str(RC4('key').encode_str('test'))
        'test'

        :param key:
        :param skip:
        """
        self.i = 0
        self.j = 0
        self.S = self.KSA(key)

    def KSA(self, key):
        """
        Key Scheduling Algorithm (from wikipedia):

        for i from 0 to 255
            S[i] := i
        endfor
        j := 0
        for i from 0 to 255
            j := (j + S[i] + key[i mod keylength]) mod 256
            swap values of S[i] and S[j]
        endfor

        :param key:
        :return: new S box
        """
        if isinstance(key, str):
            key = [ord(char) for char in key]  # key.encode('utf8')

        key_length = len(key)
        S = list(range(256))

        j = 0
        for i in range(256):
            j = (j + S[i] + key[i % key_length]) & 0xFF
            S[i], S[j] = S[j], S[i]

        return S

    def PRGA(self, size):
        """
        Psudo Random Generation Algorithm (from wikipedia):
        i := 0
        j := 0
        while GeneratingOutput:
            i := (i + 1) mod 256
            j := (j + S[i]) mod 256
            swap values of S[i] and S[j]
            K := S[(S[i] + S[j]) mod 256]
            output K
        endwhile

        :param size:
        :return:
        """
        key_stream = []

        # while GeneratingOutput:
        for _ in range(size):
            self.i = (self.i + 1) & 0xFF
            self.j = (self.j + self.S[self.i]) & 0xFF
            self.S[self.i], self.S[self.j] = self.S[self.j], self.S[self.i]
            K = self.S[(self.S[self.i] + self.S[self.j]) & 0xFF]
            key_stream.append(K)

        return key_stream

    def encode_decode(self, content_bytes):
        key_stream = self.PRGA(len(content_bytes))
        return bytes([content_bytes[i] ^ key_stream[i] for i in range(len(content_bytes))])

    def encode_str(self, input_str):
        return list(self.encode_decode(input_str.encode('utf8')))

    def decode_str(self, input_bytes):
        return self.encode_decode(input_bytes).decode('utf8')


class RC4A(RC4):
    def __init__(self, key, skip=0):
        """
        >>> RC4A('key').encode_str('test')
        [127, 110, 31, 24]
        >>> RC4A('key').decode_str(RC4A('key').encode_str('test'))
        'test'

        >>> RC4A('key', 1234).encode_str('test')
        [250, 235, 192, 199]
        >>> RC4A('key', 1234).decode_str(RC4A('key', 1234).encode_str('test'))
        'test'

        :param key:
        :param skip:
        """
        super(RC4A, self).__init__(key)
        self.S2 = self.KSA(key)
        self.j2 = 0

        # to toggle the PRGA between S boxes
        self.first_op = True

        if skip > 0:
            self.PRGA(skip)

    def PRGA(self, size):
        key_stream = []

        for _ in range(size):
            if self.first_op:
                self.first_op = False

                self.i = (self.i + 1) & 0xFF
                self.j = (self.j + self.S[self.i]) & 0xFF
                self.S[self.i], self.S[self.j] = self.S[self.j], self.S[self.i]
                K = self.S2[(self.S[self.i] + self.S[self.j]) & 0xFF]
                key_stream.append(K)

            else:
                self.first_op = True

                self.j2 = (self.j2 + self.S2[self.i]) & 0xFF
                self.S2[self.i], self.S2[self.j2] = self.S2[self.j2], self.S2[self.i]
                K = self.S[(self.S2[self.i] + self.S2[self.j2]) & 0xFF]
                key_stream.append(K)

        return key_stream


class VMPC(RC4):
    def __init__(self, key, skip=0):
        """
        >>> VMPC('key').encode_str('test')
        [19, 95, 153, 146]
        >>> VMPC('key').decode_str(VMPC('key').encode_str('test'))
        'test'

        :param key:
        :param skip:
        """
        super(VMPC, self).__init__(key)

        if skip > 0:
            self.PRGA(skip)

    def PRGA(self, size):
        key_stream = []

        for _ in range(size):
            a = self.S[self.i]
            self.j = self.S[(self.j + a) & 0xFF]
            b = self.S[self.j]

            K = self.S[(self.S[b] + 1) & 0xFF]
            key_stream.append(K)

            self.S[self.i] = b
            self.S[self.j] = a
            self.i = (self.i + 1) & 0xFF

        return key_stream


class RCPlus(RC4):
    def __init__(self, key, skip=0):
        """
        >>> RCPlus('key').encode_str('test')
        [39, 207, 224, 135]
        >>> RCPlus('key').decode_str(RCPlus('key').encode_str('test'))
        'test'

        :param key:
        :param skip:
        """
        super(RCPlus, self).__init__(key)

        if skip > 0:
            self.PRGA(skip)

    def PRGA(self, size):
        key_stream = []

        for _ in range(size):
            self.i = (self.i + 1) & 0xFF
            a = self.S[self.i]

            self.j = (self.j + a) & 0xFF
            b = self.S[self.j]

            self.S[self.i] = b
            self.S[self.j] = a

            v = (self.i << 5 ^ self.j >> 3) & 0xFF
            w = (self.j << 5 ^ self.i >> 3) & 0xFF

            c = (self.S[v] + self.S[self.j] + self.S[w]) & 0xFF
            K = (self.S[(a + b) % 256] + self.S[c ^ 0xAA]) & 0xFF ^ self.S[(self.j + b) & 0xFF]

            key_stream.append(K)

        return key_stream


class RCDrop(RC4):
    """
    The paper by Ilya Mironov says:

     - Our most conservative recommendation is based on the experimental data on the tail probability of the strong
       uniform time T (Section 5.5).

     - This means that discarding the initial 12 * 256 bytes most likely eliminates the possibility of a strong attack.

     - Dumping several times more than 256 bytes from the output stream (twice or three times this number) appears
       to be just as reasonable a precaution.

     - We recommend doing so in most applications.

    I.e. the "most conservative" recommendation is to use RC4-drop(3072),
         but RC4-drop(768) "appears to be just as reasonable".

    The latter is the default for this algorithm.
    """

    def __init__(self, key, skip=768):
        """
        >>> RCDrop('key', 4096).encode_str('test')
        [101, 75, 195, 218]
        >>> RCDrop('key', 4096).decode_str(RCDrop('key', 4096).encode_str('test'))
        'test'

        :param key:
        :param skip:
        """
        super(RCDrop, self).__init__(key)

        if skip > 0:
            self.PRGA(skip)


def _encrypt_to_hex(key, text):
    """
    # Test case 1
    # key = 'Key' # '4B6579' in hex
    # plaintext = 'Plaintext'
    # ciphertext = 'BBF316E8D940AF0AD3'
    >>> _encrypt_to_hex('Key', 'Plaintext')
    'BBF316E8D940AF0AD3'

    # Test case 2
    # key = 'Wiki' # '57696b69'in hex
    # plaintext = 'pedia'
    # ciphertext = 1021BF0420
    >>> _encrypt_to_hex('Wiki', 'pedia')
    '1021BF0420'

    # Test case 3
    # key = 'Secret' # '536563726574' in hex
    # plaintext = 'Attack at dawn'
    # ciphertext = 45A01F645FC35B383552544B9BF5
    >>> _encrypt_to_hex('Secret', 'Attack at dawn')
    '45A01F645FC35B383552544B9BF5'

    :param key:
    :param plaintext:
    :return:
    """
    return codecs.encode(bytes(rc4(key.encode('ascii'), text.encode('utf8'))), 'hex_codec').decode('ascii').upper()


def _decrypt_from_hex(key, text):
    """
    # Test case 1
    # key = 'Key' # '4B6579' in hex
    # plaintext = 'Plaintext'
    # ciphertext = 'BBF316E8D940AF0AD3'
    >>> _decrypt_from_hex('Key', 'BBF316E8D940AF0AD3')
    'Plaintext'

    # Test case 2
    # key = 'Wiki' # '57696b69'in hex
    # plaintext = 'pedia'
    # ciphertext = 1021BF0420
    >>> _decrypt_from_hex('Wiki', '1021BF0420')
    'pedia'

    # Test case 3
    # key = 'Secret' # '536563726574' in hex
    # plaintext = 'Attack at dawn'
    # ciphertext = 45A01F645FC35B383552544B9BF5
    >>> _decrypt_from_hex('Secret', '45A01F645FC35B383552544B9BF5')
    'Attack at dawn'

    :param key:
    :param plaintext:
    :return:
    """
    return rc4(key.encode('ascii'), codecs.decode(text, 'hex_codec')).decode('utf8')


if __name__ == '__main__':
    # does it crash
    RC4('key').PRGA(4096)
    RC4A('key').PRGA(4096)
    VMPC('key').PRGA(4096)
    RCDrop('key', 4096).PRGA(4096)
    RCPlus('key').PRGA(4096)

    print('RC4', RC4('key').encode_str('test'))
    # [127, 9, 71, 153]
    print(RC4('key').decode_str(RC4('key').encode_str('test')))
    # test

    print('RC4A', RC4A('key').encode_str('test'))
    # [127, 110, 31, 24]
    print(RC4A('key').decode_str(RC4A('key').encode_str('test')))
    # test

    print('RC4A-drop', RC4A('key', 1234).encode_str('test'))
    # [250, 235, 192, 199]
    print(RC4A('key', 1234).decode_str(RC4A('key', 1234).encode_str('test')))
    # test

    print('VMPC', VMPC('key').encode_str('test'))
    # [19, 95, 153, 146]
    print(VMPC('key').decode_str(VMPC('key').encode_str('test')))
    # test

    print('RCDrop', RCDrop('key', 4096).encode_str('test'))
    # [101, 75, 195, 218]
    print(RCDrop('key', 4096).decode_str(RCDrop('key', 4096).encode_str('test')))
    # test

    print('RCPlus', RCPlus('key').encode_str('test'))
    # [39, 207, 224, 135]
    print(RCPlus('key').decode_str(RCPlus('key').encode_str('test')))
    # test
