#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random, base64

class RC4(object):
    def __init__(self, key):
        self.S = self.newSBox(key)

        self.i = 0
        self.j = 0


    def newSBox(self, key):
        S = []
        for i in range(0,256):
            S.append(i)

        j = 0
        for i in range(0, 256):
            j = (j + S[i] + ord(key[i % len(key)])) % 256
            self.swap(S, i, j)

        return S

    def swap(self, S, i, j):
        cache = S[i]
        S[i] = S[j]
        S[j] = cache

    def gen(self, size):
        i = self.i
        j = self.j
        stream = []

        while len(stream) < size:
            i = (i + 1) % 256
            j = (j + self.S[i]) % 256
            self.swap(self.S, i, j)
            K = self.S[(self.S[i] + self.S[j]) % 256]
            stream.append(K)

        self.i = i
        self.j = j

        return stream

    def encStr(self, string):
        return self.enc([ord(c) for c in string])

    def enc(self, instream):
        stream = self.gen(len(instream))
        return [instream[i] ^ stream[i] for i in range(0, len(instream))]

    def decStr(self, instream):
        return "".join([chr(c) for c in self.dec(instream)])

    def dec(self, instream):
        return self.enc(instream)

class RC4A(RC4):
    def __init__(self, key):
        super().__init__(key)
        self.S2 = self.newSBox(key)
        self.j2 = 0

    def gen(self, size):
        i = self.i
        j1 = self.j
        j2 = self.j2
        S1 = self.S
        S2 = self.S2

        stream = []

        while(len(stream) < size):
            i = (i + 1) % 256
            j1 = (j1 + S1[i]) % 256
            self.swap(S1, i, j1)
            pos1 = S1[i] + S1[j1]
            stream.append(S2[pos1 % 256])
            j2 = (j2 + S2[i]) % 256
            self.swap(S2, i, j2)
            pos2 = S2[i] + S2[j2]
            stream.append(S1[pos2 % 256])

        self.i = i
        self.j = j1
        self.j2 = j2

        return stream

class VMPC(RC4):
    def __init__(self, key):
        super().__init__(key)

    def gen(self, size):
        stream = []

        i = self.i
        j = self.j
        S = self.S

        while(len(stream) < size):
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
    def gen(self, size):
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


class RC_Drop(RC4):
    def __init__(self, key, skip):
        super().__init__(key)
        self.skip = skip
        vals = [x for x in range(0, self.skip)]
        drops = self.gen(skip)

        for i in range(0, self.skip):
            dropped = vals[i] ^ drops[i]

def main():
    RC4('key').gen(4096)
    RC4A('key').gen(4096)
    VMPC('key').gen(4096)
    RC_Drop('key', 4096).gen(4096)
    RCPlus('key').gen(4096)

    print(RC4('key').encStr('test'))
    print(RC4('key').decStr(RC4('key').encStr('test')))

    print(RC4A('key').encStr('test'))
    print(RC4A('key').decStr(RC4A('key').encStr('test')))

    print(VMPC('key').encStr('test'))
    print(VMPC('key').decStr(VMPC('key').encStr('test')))

    print(RC_Drop('key', 4096).encStr('test'))
    print(RC_Drop('key', 4096).decStr(RC_Drop('key', 4096).encStr('test')))

    print(RCPlus('key').encStr('test'))
    print(RCPlus('key').decStr(RCPlus('key').encStr('test')))


if __name__ == '__main__':
    main()