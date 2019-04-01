import hashlib
import os
import base64

from py7z import archive_create
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

if __name__ == '__main__':
    source_folder = r'D:\PyCharm\wire'

    new_archive_name = os.path.basename(source_folder) + '.7z'
    new_archive_password = 'password'
    assert not os.path.exists(new_archive_name)

    print archive_create([source_folder],
                   archive=new_archive_name,
                   password=new_archive_password,
                   encrypt_headers=True
                   )

    print archive_test(new_archive_name, new_archive_password)

    raw_data = None
    with open(new_archive_name,'rb') as f:
        raw_data = f.read()

    hash_obj = hashlib.sha1()
    hash_obj.update(raw_data)
    base_64_name = hash_obj.hexdigest().upper()+'.txt'

    with open(base_64_name, 'w') as f:
        f.write(base64.b64encode(raw_data))

    os.remove(new_archive_name)

    print os.path.abspath(base_64_name)





