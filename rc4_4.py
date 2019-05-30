import codecs


class RC4(object):
    def __init__(self, key):
        self.S = self.newSBox(key)

        self.i = 0
        self.j = 0

    def newSBox(self, key):
        if isinstance(key, str):
            key = key.encode('utf8')
            # key = [ord(char) for char in key]

        S = list(range(256))

        j = 0
        for i in range(256):
            j = (j + S[i] + key[i % len(key)]) % 256
            S[i], S[j] = S[j], S[i]

        return S

    def generate_key_stream(self, size):
        i = self.i
        j = self.j
        stream = []

        while len(stream) < size:
            i = (i + 1) % 256
            j = (j + self.S[i]) % 256
            self.S[i], self.S[j] = self.S[j], self.S[i]
            stream.append(self.S[(self.S[i] + self.S[j]) % 256])

        self.i = i
        self.j = j

        return stream

    def encode_bytes(self, input_bytes):
        stream = self.generate_key_stream(len(input_bytes))
        return [input_bytes[i] ^ stream[i] for i in range(len(input_bytes))]

    def decode_bytes(self, input_bytes):
        return self.encode_bytes(input_bytes)

    def encode_str(self, input_str):
        return self.encode_bytes([ord(c) for c in input_str])

    def decode_str(self, input_str):
        return "".join([chr(c) for c in self.decode_bytes(input_str)])


class RC4A(RC4):
    def __init__(self, key):
        super().__init__(key)
        self.S2 = self.newSBox(key)
        self.j2 = 0

    def generate_key_stream(self, size):
        i = self.i
        j1 = self.j
        j2 = self.j2
        S1 = self.S
        S2 = self.S2

        stream = []

        while len(stream) < size:
            i = (i + 1) % 256

            j1 = (j1 + S1[i]) % 256
            S1[i], S1[j1] = S1[j1], S1[i]
            pos1 = S1[i] + S1[j1]
            stream.append(S2[pos1 % 256])

            j2 = (j2 + S2[i]) % 256
            S2[i], S2[j2] = S2[j2], S2[i]
            pos2 = S2[i] + S2[j2]
            stream.append(S1[pos2 % 256])

        self.i = i
        self.j = j1
        self.j2 = j2

        return stream


class VMPC(RC4):
    def __init__(self, key):
        super().__init__(key)

    def generate_key_stream(self, size):
        stream = []

        i = self.i
        j = self.j
        S = self.S

        while len(stream) < size:
            a = S[i]
            j = S[(j + a) % 256]
            b = S[j]

            stream.append(S[(S[b] + 1) % 256])

            S[i] = b
            S[j] = a
            i = (i + 1) % 256

        self.i = i
        self.j = j
        self.S = S

        return stream


class RCPlus(RC4):
    def generate_key_stream(self, size):
        i = self.i
        S = self.S
        j = self.j
        stream = []
        while len(stream) < size:
            i = (i + 1) % 256
            a = S[i]
            j = (j + a) % 256
            b = S[j]
            S[i] = b
            S[j] = a
            v = (i << 5 ^ j >> 3) % 256
            w = (j << 5 ^ i >> 3) % 256

            c = (S[v] + S[j] + S[w]) % 256
            ab = (a + b) % 256
            jb = (j + b) % 256
            stream.append((S[ab] + S[c ^ 0xAA]) ^ S[jb])

        self.i = i
        self.S = S
        self.j = j

        return stream


class RCDrop(RC4):
    """
    The paper by Ilya Mironov says:

     - Our most conservative recommendation is based on the experimental data on the tail probability of the strong
       uniform time T (Section 5.5).

     - This means that discarding the initial 12 × 256 bytes most likely eliminates the possibility of a strong attack.

     - Dumping several times more than 256 bytes from the output stream (twice or three times this number) appears
       to be just as reasonable a precaution.

     - We recommend doing so in most applications.

    I.e. the "most conservative" recommendation is to use RC4-drop(3072),
         but RC4-drop(768) "appears to be just as reasonable".

    The latter is the default for this algorithm.
    """

    def __init__(self, key, skip=768):
        super().__init__(key)
        self.generate_key_stream(skip)


def main():
    RC4('key').generate_key_stream(4096)
    RC4A('key').generate_key_stream(4096)
    VMPC('key').generate_key_stream(4096)
    RCDrop('key', 4096).generate_key_stream(4096)
    RCPlus('key').generate_key_stream(4096)

    print(RC4('key').encode_str('test'))
    print(RC4('key').decode_str(RC4('key').encode_str('test')))

    print(RC4A('key').encode_str('test'))
    print(RC4A('key').decode_str(RC4A('key').encode_str('test')))

    print(VMPC('key').encode_str('test'))
    print(VMPC('key').decode_str(VMPC('key').encode_str('test')))

    print(RCDrop('key', 4096).encode_str('test'))
    print(RCDrop('key', 4096).decode_str(RCDrop('key', 4096).encode_str('test')))

    print(RCPlus('key').encode_str('test'))
    print(RCPlus('key').decode_str(RCPlus('key').encode_str('test')))


def encrypt(key, plaintext):
    return codecs.encode(bytes(RC4(key).encode_str(plaintext)), 'hex_codec').decode('ascii').upper()


def decrypt(key, plaintext):
    return RC4(key).decode_str(codecs.decode(plaintext, 'hex_codec'))


def test():
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
    assert (encrypt('Secret',
                    'Attack at dawn')) == '45A01F645FC35B383552544B9BF5'
    assert (decrypt('Secret',
                    '45A01F645FC35B383552544B9BF5')) == 'Attack at dawn'


if __name__ == '__main__':
    test()
    main()
