"""Instructional implementation of Ron's Cipher #4 (AKA RC4).
Follows form of a `Programming Praxis exercise`_.

.. _Programming Praxis exercise:
    http://programmingpraxis.com/2009/09/04/rons-cipher-4/

:author: Christopher D. Leary <cdleary@gmail.com>
"""

import textwrap

try:
    import readline
except ImportError:  # Only available on POSIX, but no big deal.
    pass


def initialize(key):
    """Produce a 256-entry list based on `key` (a sequence of numbers)
    as the first step in RC4.
    Note: indices in key greater than 255 will be ignored.
    """
    k = list(range(256))
    j = 0
    for i in range(256):
        j = (j + k[i] + key[i % len(key)]) % 256
        k[i], k[j] = k[j], k[i]
    return k


def gen_random_bytes(k):
    """Yield a pseudo-random stream of bytes based on 256-byte array `k`."""
    i = 0
    j = 0
    while True:
        i = (i + 1) % 256
        j = (j + k[i]) % 256
        k[i], k[j] = k[j], k[i]
        yield k[(k[i] + k[j]) % 256]


def run_rc4(k, text):
    cipher_chars = []
    random_byte_gen = gen_random_bytes(k)
    for char in text:
        byte = ord(char)
        cipher_byte = byte ^ next(random_byte_gen)
        cipher_chars.append(chr(cipher_byte))
    return ''.join(cipher_chars)


# Command line interface functionality follows.


def loop_user_query(k):
    """Raises EOFError when the user uses an EOT escape sequence (i.e. ^D)."""
    while True:
        text = input('Enter plain or cipher text: ')
        stuff = run_rc4(list(k), text)
        print('Your RC4 text is:', repr(stuff))

        print('decoded', run_rc4(list(k), stuff))
        print()


def print_prologue():
    title = 'RC4 Utility'
    print('=' * len(title))
    print(title)
    print('=' * len(title))
    explanation = """The output values are valid Python strings. They may
contain escape characters of the form \\xhh to avoid confusing your terminal
emulator. Only the first 256 characters of the encryption key are used."""
    for line in textwrap.wrap(explanation, width=79):
        print(line)
    print()


def main():
    """Present a command-line interface to the cipher."""
    print_prologue()
    # Acquire initial cipher values.
    key = input('Enter an encryption key: ')
    print()
    key = [ord(char) for char in key]
    k = initialize(key)
    # Perform cipher until exit.
    try:
        loop_user_query(k)
    except EOFError:
        print()
        print('Have a pleasant day!')


if __name__ == '__main__':
    main()
