import os

import py7z
from .fragmented_file import restore_files

if __name__ == '__main__':
    source_folder = os.path.abspath(r'b64_input')
    if not os.path.exists(source_folder):
        os.makedirs(source_folder)

    target_folder = os.path.abspath(r'b64_output')
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)

    temp_archive_path = u'temp.7z'
    temp_archive_password = u'password'
    assert not os.path.exists(temp_archive_path)

    for temp_archive_path in set(restore_files(source_folder, target_folder)):
        py7z.archive_test(temp_archive_path, temp_archive_password)

        py7z.archive_extract(temp_archive_path,
                                   into_dir=target_folder,
                                   password=temp_archive_password,
                                   )

        os.remove(temp_archive_path)
