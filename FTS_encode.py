import os

import py7z
from .fragmented_file import fragment_file

if __name__ == '__main__':
    source_folder = r'C:\Users\Avery\Desktop\stuff'
    output_folder = r'b64_input'

    new_archive_path = os.path.basename(source_folder) + u'.7z'
    new_archive_password = u'password'
    assert not os.path.exists(new_archive_path)

    py7z.archive_create([source_folder],
                        archive=new_archive_path,
                        password=new_archive_password,
                        encrypt_headers=True
                        )

    py7z.archive_test(new_archive_path, new_archive_password)

    # fragment_file(new_archive_path, output_folder,max_size=1000000,size_range=300000)
    fragment_file(new_archive_path, output_folder)
    os.remove(new_archive_path)
