"""
fragment a file into multiple smaller ascii files
"""
import codecs
import hashlib
import json
import random
import time
import warnings
from base64 import a85decode
from base64 import a85encode
from os import urandom
from pathlib import Path
from typing import Generator
from typing import List
from typing import Optional

from frag_rc4 import rc4
from frag_utils import format_bytes
from frag_utils import hash_content
from frag_utils import hash_file
from frag_utils import password_to_bytes

MAGIC_STRING = 'text/fragment+a85+rc4+ver3'  # follow mime type convention approximately because why not
HASH_FUNCTION = 'sha1'  # or any of {'md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512'}


def fragment_file(file_path: Path,
                  output_dir: Path,
                  password: Optional[str] = None,
                  max_size: int = 22000000,
                  size_range: int = 4000000,
                  verbose: bool = False
                  ) -> List[Path]:
    """
    see TextFragment for details
    """
    # sanity checks
    assert file_path.exists(), f'input file does not exist at {file_path}'
    assert 0 <= size_range < max_size

    # allocate fragment sizes greedily and randomly
    unallocated_bytes = file_path.stat().st_size
    fragment_sizes = []
    min_size = max_size - size_range
    while unallocated_bytes > max_size:
        fragment_size = random.randint(min_size, max_size)  # min_size <= fragment_size <= max_size
        fragment_sizes.append(fragment_size)
        unallocated_bytes -= fragment_size
    if unallocated_bytes:
        fragment_sizes.append(unallocated_bytes)
    assert sum(fragment_sizes) == file_path.stat().st_size
    random.shuffle(fragment_sizes)  # otherwise the smallest fragment is always at the end

    # get static values used in header info
    file_name = file_path.name
    file_hash = hash_file(file_path, hash_func=HASH_FUNCTION)
    file_size = file_path.stat().st_size
    if verbose:
        print(f'fragmentation target path is <{file_path}>')
        print(f'fragmentation target hash is {file_hash}')
        print(f'fragmentation target size is {format_bytes(file_size)}')
        print(f'creating {len(fragment_sizes)} fragments...')

    # create output folder
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    assert output_dir.is_dir()

    # iterate through input file only once
    fragment_paths = []
    with file_path.open('rb') as f_in:
        for fragment_idx, fragment_size in enumerate(fragment_sizes):
            # get start byte
            fragment_start = f_in.tell()

            # read raw data
            fragment_raw = f_in.read(fragment_size)

            # hash data
            fragment_hash = hash_content(fragment_raw, HASH_FUNCTION)

            # always generate salt and IV
            password_salt = urandom(256)  # match rc4 keylen = 256 bytes
            initialization_vector = urandom(16)  # match rc4 IV len = 16 bytes

            # encrypt data if password was provided (even if password is an empty string)
            if password is not None:
                password_bytes = password_to_bytes(password, salt=password_salt, length=256)  # match rc4 keylen
                fragment_encrypted = rc4(password_bytes, fragment_raw, initialization_vector=initialization_vector)

            # don't encrypt data if password was not provided (salt and IV generated and saved but not used)
            else:
                fragment_encrypted = fragment_raw

            if verbose:
                print(f'fragment [{fragment_idx + 1}/{len(fragment_sizes)}] {fragment_hash}'
                      f' -> {format_bytes(fragment_size)} from byte {fragment_start}')

            # generate json header
            initialization_vector_hex = codecs.encode(initialization_vector, 'hex_codec').decode('ascii').upper()
            password_salt_hex = codecs.encode(password_salt, 'hex_codec').decode('ascii').upper()
            header = json.dumps({'file_name':             file_name.encode('idna').decode('ascii'),
                                 'file_hash':             file_hash,
                                 'file_size':             file_size,
                                 'fragment_start':        fragment_start,
                                 'fragment_hash':         fragment_hash,
                                 'fragment_size':         fragment_size,
                                 'initialization_vector': initialization_vector_hex,
                                 'password_salt':         password_salt_hex,
                                 }, separators=(',', ':'))

            # write fragment file
            fragment_path = output_dir / f'{fragment_hash}.txt'
            fragment_tmp_path = output_dir / f'{fragment_hash}.txt.tempfile'
            fragment_paths.append(fragment_path)
            try:
                with fragment_tmp_path.open(mode='wt', encoding='ascii', newline='\n') as f_out:
                    f_out.write(MAGIC_STRING + '\n')
                    f_out.write(header + '\n')
                    f_out.write(a85encode(fragment_encrypted).decode('ascii') + '\n')
                fragment_tmp_path.rename(fragment_path)

            except Exception:
                if fragment_tmp_path.exists():
                    fragment_tmp_path.unlink()
                raise

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
        initialization_vector:  <initialization vector> (base64)
    """

    def __init__(self, fragment_path: Path, password: Optional[str] = None):
        self.fragment_path = fragment_path
        self.password = password

        # verify magic string and read header
        with fragment_path.open(mode='rt', encoding='ascii') as f:
            assert f.readline().strip() == MAGIC_STRING
            header = json.loads(f.readline())
            self.content_pos = f.tell()

        # parse header
        self.file_name: str = header['file_name'].encode('ascii').decode('idna')
        self.file_hash: str = header['file_hash']
        self.file_size: int = header['file_size']
        self.fragment_start: int = header['fragment_start']
        self.fragment_hash: str = header['fragment_hash']
        self.fragment_size: int = header['fragment_size']
        self.initialization_vector: bytes = codecs.decode(header['initialization_vector'].encode('ascii'), 'hex_codec')
        self.password_salt: bytes = codecs.decode(header['password_salt'].encode('ascii'), 'hex_codec')

    def read(self, length=None):
        """
        get decoded raw content of fragment
        :return: content (bytes)
        """
        # sanity check
        if length is None:
            length = self.fragment_size
        assert length <= self.fragment_size

        with self.fragment_path.open(mode='rt', encoding='ascii') as f:
            # read and decode content to bytes
            f.seek(self.content_pos)
            decoded_content = a85decode(f.readline().rstrip())

            # decrypt data
            if self.password is not None:
                password_bytes = password_to_bytes(self.password, salt=self.password_salt, length=256)
                decrypted_content = rc4(password_bytes, decoded_content,
                                        initialization_vector=self.initialization_vector)

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
            if self.fragment_path.exists():
                if retry:
                    print(f'retrying file deletion for <{self.fragment_path}>...')
                    time.sleep(1)
                try:
                    self.fragment_path.unlink()
                except PermissionError as e:
                    err = f'[Windows Error] {e.args[1]}: {repr(e.filename)}'
                except FileNotFoundError:
                    pass
        if self.fragment_path.exists():
            warnings.warn(f'unable to delete fragment at path {self.fragment_path}')
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
                print(f'file {self.file_hash} is missing a fragment starting at byte {curr_byte}')
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

    def make_file(self, output_dir: Path,
                  file_name: Optional[str] = None,
                  remove_originals: bool = True,
                  overwrite: bool = False,
                  verbose: bool = False
                  ) -> Optional[Path]:

        # which fragment_set to make from
        extraction_plan = self.get_extraction_plan()
        assert extraction_plan is not None

        if verbose:
            print(f'restoring {format_bytes(self.file_size)} from {len(extraction_plan)} fragments of {self.file_name}')
            unused = sum(len(fragments) for fragments in self.fragments.values()) - len(extraction_plan)
            if unused and remove_originals:
                print(f'{unused} extra fragment(s) will also be deleted')

        # where output file will be written
        if file_name is None:
            file_name = self.file_name
        file_path = output_dir / file_name

        # make parent dir (not based on output_dir because file_name can contain subdir info)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        assert file_path.parent.is_dir()

        # check if already extracted to avoid overwrite
        if file_path.exists():
            if hash_file(file_path, hash_func=HASH_FUNCTION) == self.file_hash:
                if verbose:
                    print('file already extracted successfully, exists at output path')
                if remove_originals:
                    self.remove()
                return file_path

            if not overwrite:
                if verbose:
                    print('non-matching file already exists at output path, skipping')
                warnings.warn(f'file already exists: {file_path}')
                return None

        # start extraction
        temp_path = file_path.with_suffix(file_path.suffix + '.partial')
        try:
            with temp_path.open('wb') as f:
                # init full content hash
                hash_obj = getattr(hashlib, HASH_FUNCTION)()

                # write all fragments in order and update full content hash
                for fragment_idx, (required_length, text_fragment) in enumerate(extraction_plan):
                    if verbose:
                        print(f'reading fragment [{fragment_idx + 1}/{len(extraction_plan)}]'
                              f' {text_fragment.fragment_hash}'
                              f' -> {format_bytes(text_fragment.fragment_size)}'
                              f' from byte {text_fragment.fragment_start}')

                    assert f.tell() == text_fragment.fragment_start
                    content = text_fragment.read(required_length)
                    hash_obj.update(content)
                    f.write(content)

                # make sure full and correct file contents have been written to disk
                assert f.tell() == self.file_size
                assert self.file_hash == hash_obj.hexdigest().upper()
            temp_path.rename(file_path)

        # if something failed, delete partial file
        except Exception:
            if temp_path.exists():
                temp_path.unlink()
            raise

        # erase originals (unless otherwise specified) and return
        if remove_originals:
            self.remove()
        return file_path


def defragment_files(input_dir: Path,
                     password: Optional[str] = None,
                     file_name: Optional[str] = None,
                     remove_originals: bool = True,
                     overwrite: bool = False,
                     verbose: bool = False
                     ) -> Generator[Path, None, None]:
    fragmented_files = dict()

    input_dir = input_dir.resolve()
    for txt_path in input_dir.glob('*'):
        if not txt_path.is_file():
            continue
        with txt_path.open('rt') as f:
            if f.read(len(MAGIC_STRING)) != MAGIC_STRING:
                continue
        text_fragment = TextFragment(txt_path, password=password)
        fragmented_files.setdefault(text_fragment.file_hash, FragmentedFile(text_fragment)).add(text_fragment)

    for file_hash, file_fragments in fragmented_files.items():
        assert isinstance(file_fragments, FragmentedFile)
        if file_fragments.get_extraction_plan() is not None:
            out_path = file_fragments.make_file(output_dir=input_dir,
                                                file_name=file_name,
                                                remove_originals=remove_originals,
                                                overwrite=overwrite,
                                                verbose=verbose)

            if out_path is not None:
                if verbose:
                    print(f'saved {file_hash} to path: {out_path}')
                yield out_path

            else:
                if verbose:
                    print(f'skipped restoration of {file_hash}')
                else:
                    warnings.warn(f'skipped restoration of {file_hash}')

        elif verbose:
            print(f'incomplete file: {file_hash} with name {file_fragments.file_name}')
