import base64
import fnmatch
import hashlib
import json
import os
import random

import datetime


def crawl(top, file_pattern='*'):
    """generator giving all file paths"""
    for root_path, dir_list, file_list in os.walk(unicode(top)):
        for file_name in fnmatch.filter(file_list, file_pattern):
            yield os.path.join(root_path, file_name)


def hash_file(file_path, hash_func='SHA1'):
    hash_func = hash_func.strip().lower()
    assert hash_func in ['md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512']
    hash_obj = getattr(hashlib, hash_func)()
    f = os.open(file_path, (os.O_RDWR | os.O_BINARY))
    for block in iter(lambda: os.read(f, 65536), b''):
        hash_obj.update(block)
    os.close(f)
    return hash_obj.hexdigest().upper()


def hash_content(content, hash_func='SHA1'):
    hash_func = hash_func.strip().lower()
    assert hash_func in ['md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512']
    hash_obj = getattr(hashlib, hash_func)()
    hash_obj.update(content)
    return hash_obj.hexdigest().upper()


def format_bytes(num):
    unit = 0
    while num >= 1024 and unit < 8:
        num /= 1024.0
        unit += 1
    unit = ['Bytes', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB'][unit]
    return (u'%.2f %s' if num % 1 else u'%d %s') % (num, unit)


def fragment_file(file_path, into_dir, max_size=22000000, size_range=4000000, hash_func='SHA1'):
    file_path = os.path.abspath(unicode(file_path))
    file_size = os.path.getsize(file_path)
    fragment_sizes = []
    assert size_range < max_size
    min_size = max_size - size_range
    while file_size > max_size:
        fragment_size = random.randint(min_size, max_size)
        fragment_sizes.append(fragment_size)
        file_size -= fragment_size
    if file_size:
        fragment_sizes.append(file_size)
    assert sum(fragment_sizes) == os.path.getsize(file_path)

    output_dir = os.path.abspath(into_dir)
    if not os.path.isdir(output_dir):
        assert not os.path.exists(output_dir)
        os.makedirs(output_dir)

    metadata = {'name': os.path.basename(file_path),
                'hash': hash_file(file_path, hash_func=hash_func),
                'size': os.path.getsize(file_path),
                'time': datetime.datetime.now().isoformat()
                }

    ordered_manifest = []
    with open(file_path, 'rb') as f:
        for i, fragment_size in enumerate(fragment_sizes):
            ordered_manifest.append((hash_content(f.read(fragment_size), hash_func=hash_func), (fragment_size, i)))
        assert len(f.read()) == 0
    manifest = dict(ordered_manifest)

    paths = []
    with open(file_path, 'rb') as f:
        for content_hash, (fragment_size, fragment_index) in ordered_manifest:
            header = json.dumps({'hash':     content_hash,
                                 'metadata': metadata,
                                 'manifest': manifest,
                                 })
            text_fragment_path = os.path.join(output_dir, content_hash + '.txt')
            paths.append(text_fragment_path)
            with open(text_fragment_path, 'w') as f2:
                f2.write('text/fragment\n')
                f2.write(header + '\n')
                f2.write(base64.b64encode(f.read(fragment_size)).decode('ascii'))
        assert len(f.read()) == 0

    # # verbose
    # print('METADATA')
    # pprint.pprint(metadata)
    # print('MANIFEST')
    # pprint.pprint(manifest)

    return paths


class TextFragment(object):
    """
    parse a fragment.txt file which has three lines of ascii
    1st line is the string "text/fragment"
    2nd line is a json header
    3rd line is base64-encoded binary content
    
    json-header:
        hash: <content hash>
        metadata: 
            name: <file name>
            hash: <file hash>
            size: <file size>
            time: <file creation datetime in iso format>
        manifest:
            <content hash>: <content size>, <index>
    """

    def __init__(self, file_path, hash_func='SHA1'):
        with open(file_path) as f:
            assert f.readline().strip() == 'text/fragment'
            header = json.loads(f.readline())
            self.content_pos = f.tell()
        self.hash_func = hash_func
        self.file_path = file_path
        self.content_hash = header['hash']
        self.metadata = header['metadata']
        self.manifest = header['manifest']
        self.fragment_set = self.metadata['hash'] + self.metadata['time']
        self.content_size, self.index = self.manifest[self.content_hash]

    def read(self):
        with open(self.file_path) as f:
            f.seek(self.content_pos)
            content = base64.b64decode(f.readline().rstrip())  # bytes
            assert self.content_size == len(content)
            assert self.content_hash == hash_content(content, hash_func=self.hash_func)
            return content

    def remove(self):
        os.remove(self.file_path)


class FragmentSet(object):
    def __init__(self, metadata, manifest, hash_func='SHA1'):
        """
        :type metadata: dict
        :type manifest: dict
        """
        self.hash_func = hash_func.strip().lower()
        assert self.hash_func in ['md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512']
        self.file_name = metadata['name']
        self.file_hash = metadata['hash']
        self.file_size = metadata['size']
        self.fragments = dict()
        fragment_indices = []
        for (fragment_hash, (fragment_size, fragment_index)) in manifest.items():
            self.fragments[fragment_hash] = []
            fragment_indices.append((fragment_index, fragment_size, fragment_hash))
        self.ordering = []
        file_pos = 0
        for fragment_index, fragment_size, fragment_hash in sorted(fragment_indices):
            self.ordering.append((fragment_hash, file_pos))
            file_pos += fragment_size
        assert file_pos == self.file_size
        assert len(self.ordering) == len(self.fragments)

    def add(self, text_fragment):
        """
        :type text_fragment: TextFragment
        """
        assert text_fragment.content_hash in self.fragments
        self.fragments[text_fragment.content_hash].append(text_fragment)

    def is_complete(self):
        return all(len(seen) > 0 for frag, seen in self.fragments.items())

    def make_file(self, into_dir, file_name=None, remove_originals=True, overwrite=False):
        assert self.is_complete()

        if file_name is None:
            file_name = self.file_name
        file_path = os.path.abspath(os.path.join(into_dir, file_name))
        parent_dir = os.path.dirname(file_path)
        if not os.path.isdir(parent_dir):
            assert not os.path.exists(parent_dir)
            os.makedirs(parent_dir)

        if not overwrite and os.path.exists(file_path):
            # don't overwrite
            print('file already exists, skipping')
            return

        with open(file_path, 'wb') as f:
            hash_obj = getattr(hashlib, self.hash_func)()

            for fragment_hash, fragment_pos in self.ordering:
                assert f.tell() == fragment_pos
                content = self.fragments[fragment_hash][0].read()
                hash_obj.update(content)
                f.write(content)

            assert f.tell() == self.file_size
            assert self.file_hash == hash_obj.hexdigest().upper()

        if remove_originals:
            for fragment_list in self.fragments.values():
                for text_fragment in fragment_list:
                    text_fragment.remove()

        return file_path


def restore_files(input_dir, output_dir):
    f_sets = dict()

    for path in crawl(input_dir):
        tf = TextFragment(path)
        f_sets.setdefault(tf.fragment_set, FragmentSet(tf.metadata, tf.manifest)).add(tf)

    output_paths = []
    for fs in f_sets.values():
        if fs.is_complete():
            output_paths.append(fs.make_file(output_dir))

    return output_paths


if __name__ == '__main__':
    fragment_file('fragmented_file.py', 'b64_input', 123, 12)
    restore_files('b64_input', 'b64_output')
    assert hash_file('fragmented_file.py') == hash_file('b64_output/fragmented_file.py')
    os.remove('b64_output/fragmented_file.py')
