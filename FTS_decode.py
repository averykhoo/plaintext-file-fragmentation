import os
import shutil

from FTS_encode_decode.fragmented_file import restore_files

source_folder = os.path.abspath(r'b64_input')
output_folder = os.path.abspath(r'b64_output')
archive_password = 'password'

if __name__ == '__main__':

    if not os.path.isdir(source_folder):
        assert not os.path.exists(source_folder)
        os.makedirs(source_folder)
        print('source folder <{PATH}> does not exist, creating...'.format(PATH=source_folder))

    if not os.path.isdir(output_folder):
        assert not os.path.exists(output_folder)
        os.makedirs(output_folder)
        print('output folder <{PATH}> does not exist, creating...'.format(PATH=output_folder))

    for temp_archive_path in restore_files(source_folder, output_folder, verbose=False):
        print('restored <{PATH}>, unpacking archive...'.format(PATH=temp_archive_path))
        shutil.unpack_archive(temp_archive_path, extract_dir=output_folder, format='bztar')
        os.remove(temp_archive_path)

    print('done!')
