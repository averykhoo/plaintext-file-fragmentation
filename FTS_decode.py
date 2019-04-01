import base64
import fnmatch
import hashlib
import os

from py7z import archive_extract
from py7z import archive_test


def hashlib_hash(file_path, hash_type='MD5'):
    hash_type = hash_type.strip().lower()
    assert hash_type in ['md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512']
    hash_func = getattr(hashlib, hash_type)()
    f = os.open(file_path, (os.O_RDWR | os.O_BINARY))
    for block in iter(lambda: os.read(f, 65536), b''):
        hash_func.update(block)
    os.close(f)
    return hash_func.hexdigest().upper()


def crawl(top, file_pattern='*'):
    """generator giving all file paths"""
    for root_path, dir_list, file_list in os.walk(top):
        for file_name in fnmatch.filter(file_list, file_pattern):
            yield os.path.join(root_path, file_name)


if __name__ == '__main__':
    source_folder = os.path.abspath(r'b64_input')
    if not os.path.exists(source_folder):
        os.makedirs(source_folder)

    target_folder = os.path.abspath(r'b64_output')
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)

    temp_archive_name = 'temp.7z'
    temp_archive_password = 'password'
    assert not os.path.exists(temp_archive_name)

    for file_path in crawl(source_folder, '*.txt'):
        print os.path.abspath(file_path)
        h = os.path.basename(file_path).split('.', 1)[0]
        with open(file_path) as f:
            raw_data = base64.b64decode(f.read())

        hash_obj = hashlib.sha1()
        hash_obj.update(raw_data)
        assert h == hash_obj.hexdigest().upper()

        with open(temp_archive_name, 'wb') as f:
            f.write(raw_data)

        print archive_test(temp_archive_name, temp_archive_password)

        print archive_extract(temp_archive_name,
                        into_dir=target_folder,
                        password=temp_archive_password
                        )

        os.remove(temp_archive_name)

