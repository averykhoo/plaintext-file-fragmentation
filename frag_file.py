"""
fragment a file into multiple smaller ascii files
"""
import base64
import glob
import hashlib
import io
import json
import os
import random
import time
import warnings

from frag_rc4 import rc4
from frag_utils import a85decode, a85encode, password_to_bytes
from frag_utils import hash_content, hash_file

MAGIC_STRING = 'text/a85+fragment+RC4'  # follow mime type convention because why not
HASH_FUNCTION = 'sha1'

assert HASH_FUNCTION in ['md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512']


def fragment_file(file_path, output_dir, password=None, max_size=22000000, size_range=4000000, verbose=False):
    """
    see TextFragment for details
    """
    # sanity checks
    assert os.path.isfile(file_path), 'input file does not exist'
    assert 0 <= size_range < max_size

    # allocate fragment sizes randomly
    unallocated_bytes = os.path.getsize(file_path)
    fragment_sizes = []
    min_size = max_size - size_range
    while unallocated_bytes > max_size:
        fragment_size = random.randint(min_size, max_size)
        fragment_sizes.append(fragment_size)
        unallocated_bytes -= fragment_size
    if unallocated_bytes:
        fragment_sizes.append(unallocated_bytes)
    assert sum(fragment_sizes) == os.path.getsize(file_path)

    # get static values used in header info
    file_name = a85encode(os.path.basename(file_path).encode('utf8'))
    file_hash = hash_file(file_path, hash_func=HASH_FUNCTION)
    file_size = os.path.getsize(file_path)
    if verbose:
        print('fragmentation target path is <{}>'.format(file_path))
        print('fragmentation target hash is <{}>'.format(file_hash))
        print('fragmentation target size is <{}>'.format(file_size))
        print('creating {} fragments...'.format(len(fragment_sizes)))

    # create output folder
    output_dir = os.path.abspath(output_dir)
    if not os.path.isdir(output_dir):
        assert not os.path.exists(output_dir)
        os.makedirs(output_dir)

    # iterate through input file only once
    fragment_paths = []
    with io.open(file_path, 'rb') as f_in:
        for fragment_size in fragment_sizes:
            # get start byte
            fragment_start = f_in.tell()

            # read raw data
            fragment_raw = f_in.read(fragment_size)

            # hash data
            hash_obj = getattr(hashlib, HASH_FUNCTION)()
            hash_obj.update(fragment_raw)
            fragment_hash = hash_obj.hexdigest().upper()

            # encrypt data
            if password is not None:
                cipher = RC4(password_to_bytes(password), RC4_DROP)
                fragment_encrypted = cipher.encode_decode(fragment_raw)
            else:
                fragment_encrypted = fragment_raw

            if verbose:
                print('fragment {} -> bytes {} through {}'.format(fragment_hash,
                                                                  fragment_start,
                                                                  fragment_start + fragment_size))

            # generate json header
            header = json.dumps({'file_name':      file_name.decode('ascii'),
                                 'file_hash':      file_hash,
                                 'file_size':      file_size,
                                 'fragment_start': fragment_start,
                                 'fragment_hash':  fragment_hash,
                                 'fragment_size':  fragment_size,
                                 }, separators=(',', ':'))

            # write fragment file
            fragment_path = os.path.join(output_dir, fragment_hash + '.txt')
            fragment_paths.append(fragment_path)
            err = None
            for _attempt in range(3):
                try:
                    with io.open(fragment_path + '.tempfile', mode='wt', encoding='ascii', newline='\n') as f_out:
                        f_out.write(MAGIC_STRING + u'\n')
                        f_out.write(header + u'\n')
                        f_out.write(a85encode(fragment_encrypted).decode('ascii') + u'\n')
                    os.rename(fragment_path + '.tempfile', fragment_path)
                    break
                except Exception:
                    if os.path.exists(fragment_path + '.tempfile'):
                        os.remove(fragment_path + '.tempfile')
                    raise
            else:
                raise err

        # make sure the entire file has been processed
        assert len(f_in.read()) == 0

    # return ordered list of fragment file paths
    return fragment_paths


class TextFragment:
    """
    parse a fragment.txt file which has three lines of ascii
    1st line is the MAGIC_STRING
    2nd line is a json header
    3rd line is base64-encoded binary content
    
    json-header:
        file_name:              <file name> (base64)
        file_hash:              <file hash> (base64)
        file_size:              <file size> (int)
        fragment_start:         <first byte of fragment data>
        fragment_hash:          <fragment hash> (base64)
        fragment_size:          <fragment size> (int)
    """

    def __init__(self, fragment_path, password=None):
        """
        :type fragment_path: str
        """
        self.fragment_path = fragment_path
        self.password = password

        # verify magic string and read header
        with io.open(fragment_path, mode='rt', encoding='ascii') as f:
            assert f.readline().strip() == MAGIC_STRING
            header = json.loads(f.readline())
            self.content_pos = f.tell()

        # parse header
        self.file_name = a85decode(header['file_name']).decode('utf8')
        self.file_hash = header['file_hash']
        self.file_size = header['file_size']
        self.fragment_start = header['fragment_start']
        self.fragment_hash = header['fragment_hash']
        self.fragment_size = header['fragment_size']

    def read(self, length=None):
        """
        get decoded raw content of fragment
        :return: content (bytes)
        """
        # sanity check
        if length is None:
            length = self.fragment_size
        assert length <= self.fragment_size

        with io.open(self.fragment_path, mode='rt', encoding='ascii') as f:
            # read and decode content to bytes
            f.seek(self.content_pos)
            decoded_content = a85decode(f.readline().rstrip())

            # decrypt data
            if self.password is not None:
                cipher = RC4(password_to_bytes(self.password), RC4_DROP)
                decrypted_content = cipher.encode_decode(decoded_content)
            else:
                decrypted_content = decoded_content

            # nothing left behind
            assert not f.read().strip()

            # verify content
            assert self.fragment_size == len(decrypted_content)
            assert self.fragment_hash == hash_content(decrypted_content, hash_func=HASH_FUNCTION)

            # return as many bytes as requested
            return decrypted_content[:length]

    def remove(self):
        """
        delete source file
        """
        err = None
        for retry in range(3):
            if os.path.exists(self.fragment_path):
                if retry:
                    print('retrying file deletion for <{}>...'.format(self.fragment_path))
                    time.sleep(1)
                try:
                    os.remove(self.fragment_path)
                except PermissionError as e:
                    err = '[Windows Error] {}: {}'.format(e.args[1], repr(e.filename))
                except FileNotFoundError:
                    pass
        if os.path.exists(self.fragment_path):
            warnings.warn('unable to delete fragment at path {}'.format(self.fragment_path))
            warnings.warn(err)


class FragmentedFile:
    def __init__(self, text_fragment):
        """
        :type text_fragment: TextFragment
        """
        # sanity check
        assert isinstance(text_fragment, TextFragment)

        # get metadata
        self.file_name = text_fragment.file_name
        self.file_hash = text_fragment.file_hash
        self.file_size = text_fragment.file_size

        # fragment storage
        self.fragments = dict()  # start byte -> [(end byte, fragment)]
        self.extraction_plan = None

        # # add first fragment
        # self.add(text_fragment)

    def add(self, text_fragment):
        """
        it is acceptable to add the same fragment multiple times
        :type text_fragment: TextFragment
        """
        # ensure it really is the same original file
        assert text_fragment.file_name == self.file_name
        assert text_fragment.file_hash == self.file_hash
        assert text_fragment.file_size == self.file_size

        # index text fragments by interval
        self.fragments \
            .setdefault(text_fragment.fragment_start, []) \
            .append((text_fragment.fragment_start + text_fragment.fragment_size, text_fragment))

    def get_extraction_plan(self, recalculate=False):
        # is work already done
        if self.extraction_plan is not None and not recalculate:
            return self.extraction_plan

        # init
        prev_byte = 0
        curr_byte = 0
        fragment_order = []
        fragment_starts = []

        # optimize plan to extract entire file
        while curr_byte < self.file_size:
            # expand the contiguous range as far as possible
            start_bytes = [frag_start for frag_start in self.fragments if prev_byte <= frag_start <= curr_byte]
            candidates = [frag for fragment_start in start_bytes for frag in self.fragments[fragment_start]]

            # if progress can't be made, then fragments are missing
            if not candidates:
                self.extraction_plan = None
                print('file {} is missing a fragment starting at byte {}'.format(self.file_hash, curr_byte))
                return None

            #
            next_byte, text_fragment = max(candidates, key=lambda x: x[0])
            prev_byte, curr_byte = curr_byte, next_byte
            fragment_order.append(text_fragment)
            fragment_starts.append(text_fragment.fragment_start)

        # do we have the entire file
        assert curr_byte == self.file_size

        # how much to extract from each fragment
        fragment_starts.append(curr_byte)
        fragment_read_bytes = [s2 - s1 for s2, s1 in zip(fragment_starts[1:], fragment_starts[:-1])]

        # save plan and return
        self.extraction_plan = list(zip(fragment_read_bytes, fragment_order))
        return self.extraction_plan

    def remove(self):
        """
        remove all files in this multiset
        """
        for fragment_set in self.fragments.values():
            for _, text_fragment in fragment_set:
                text_fragment.remove()

    def make_file(self, output_dir, file_name=None, remove_originals=True, overwrite=False, verbose=False):
        # which fragment_set to make from
        extraction_plan = self.get_extraction_plan()
        assert extraction_plan is not None

        if verbose:
            print('restoring {} bytes from {} fragments of {}'.format(self.file_size,
                                                                      len(extraction_plan),
                                                                      self.file_name))
            unused = sum(len(fragments) for fragments in self.fragments.values()) - len(extraction_plan)
            if unused and remove_originals:
                print('{} extra fragment(s) will also be deleted'.format(unused))

        # where output file will be written
        if file_name is None:
            file_name = self.file_name
        file_path = os.path.abspath(os.path.join(output_dir, file_name))

        # make parent dir (not based on output_dir because file_name can contain subdir info)
        parent_dir = os.path.dirname(file_path)
        if not os.path.isdir(parent_dir):
            assert not os.path.exists(parent_dir)
            os.makedirs(parent_dir)

        # check if already extracted to avoid overwrite
        if os.path.exists(file_path):
            if hash_file(file_path, hash_func=HASH_FUNCTION) == self.file_hash:
                if verbose:
                    print('file already successfully extracted and exists at output path')
                if remove_originals:
                    self.remove()
                return file_path

            if not overwrite:
                if verbose:
                    print('non-matching file already exists at output path, skipping')
                warnings.warn('file already exists: {}'.format(file_path))
                return None

        # start extraction
        temp_path = file_path + '.partial'
        try:
            with io.open(temp_path, 'wb') as f:
                # init full content hash
                hash_obj = getattr(hashlib, HASH_FUNCTION)()

                # write all fragments in order and update full content hash
                for required_length, text_fragment in extraction_plan:
                    if verbose:
                        print('restoring from {} -> bytes {} through {}'
                              .format(text_fragment.fragment_hash,
                                      text_fragment.fragment_start + 1,
                                      text_fragment.fragment_start + text_fragment.fragment_size))

                    assert f.tell() == text_fragment.fragment_start
                    content = text_fragment.read(required_length)
                    hash_obj.update(content)
                    f.write(content)

                # make sure full and correct file contents have been written to disk
                assert f.tell() == self.file_size
                assert self.file_hash == hash_obj.hexdigest().upper()
            os.rename(temp_path, file_path)

        # if something failed, delete partial file
        except Exception:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise

        # erase originals (unless otherwise specified) and return
        if remove_originals:
            self.remove()
        return file_path


def restore_files(input_dir, password=None, file_name=None, remove_originals=True, overwrite=False, verbose=False):
    fragmented_files = dict()

    for path in glob.glob(os.path.join(input_dir, '*.txt')):
        text_fragment = TextFragment(path, password=password)
        fragmented_files.setdefault(text_fragment.file_hash, FragmentedFile(text_fragment)).add(text_fragment)

    for file_hash, file_fragments in fragmented_files.items():
        assert isinstance(file_fragments, FragmentedFile)
        if file_fragments.get_extraction_plan() is not None:
            out_path = file_fragments.make_file(output_dir=input_dir,
                                                file_name=file_name,
                                                remove_originals=remove_originals,
                                                overwrite=overwrite,
                                                verbose=verbose)
            if verbose and out_path is not None:
                print('saved {} to path: {}'.format(file_hash, out_path))
            elif verbose:
                print('skipped restoration of {}'.format(file_hash))

            yield out_path

        elif verbose:
            print('incomplete file: {} with name {}'.format(file_hash, file_fragments.file_name))
