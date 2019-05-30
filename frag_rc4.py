class RC4(object):
    def __init__(self, key, skip=None):
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
        super(RCDrop, self).__init__(key)

        if skip > 0:
            self.PRGA(skip)


def test():
    # does it crash
    RC4('key').PRGA(4096)
    RC4A('key').PRGA(4096)
    VMPC('key').PRGA(4096)
    RCDrop('key', 4096).PRGA(4096)
    RCPlus('key').PRGA(4096)

    import codecs

    def encrypt(key, plaintext):
        return codecs.encode(bytes(RC4(key).encode_str(plaintext)), 'hex_codec').decode('ascii').upper()

    def decrypt(key, plaintext):
        return RC4(key).decode_str(codecs.decode(plaintext, 'hex_codec'))

    # Test case 1
    # key = '4B6579' # 'Key' in hex
    # key = 'Key'
    # plaintext = 'Plaintext'
    # ciphertext = 'BBF316E8D940AF0AD3'
    assert (encrypt('Key', 'Plaintext')) == 'BBF316E8D940AF0AD3', repr(encrypt('Key', 'Plaintext'))
    assert (decrypt('Key', 'BBF316E8D940AF0AD3')) == 'Plaintext', repr(decrypt('Key', 'BBF316E8D940AF0AD3'))

    # Test case 2
    # key = 'Wiki' # '57696b69'in hex
    # plaintext = 'pedia'
    # ciphertext should be 1021BF0420
    assert (encrypt('Wiki', 'pedia')) == '1021BF0420'
    assert (decrypt('Wiki', '1021BF0420')) == 'pedia'

    # Test case 3
    # key = 'Secret' # '536563726574' in hex
    # plaintext = 'Attack at dawn'
    # ciphertext should be 45A01F645FC35B383552544B9BF5
    assert (encrypt('Secret', 'Attack at dawn')) == '45A01F645FC35B383552544B9BF5'
    assert (decrypt('Secret', '45A01F645FC35B383552544B9BF5')) == 'Attack at dawn'


if __name__ == '__main__':
    test()

    print('RC4', RC4('key').encode_str('test'))
    print(RC4('key').decode_str(RC4('key').encode_str('test')))
    # [127, 9, 71, 153]
    # test

    print('RC4A', RC4A('key').encode_str('test'))
    print(RC4A('key').decode_str(RC4A('key').encode_str('test')))
    # [127, 110, 31, 24]
    # test

    print('RC4A-drop', RC4A('key', 1234).encode_str('test'))
    print(RC4A('key', 1234).decode_str(RC4A('key', 1234).encode_str('test')))

    print('VMPC', VMPC('key').encode_str('test'))
    print(VMPC('key').decode_str(VMPC('key').encode_str('test')))
    # [19, 95, 153, 146]
    # test

    print('RCDrop', RCDrop('key', 4096).encode_str('test'))
    print(RCDrop('key', 4096).decode_str(RCDrop('key', 4096).encode_str('test')))
    # [101, 75, 195, 218]
    # test

    print('RCPlus', RCPlus('key').encode_str('test'))
    print(RCPlus('key').decode_str(RCPlus('key').encode_str('test')))
    # [39, 207, 224, 135]
    # test
