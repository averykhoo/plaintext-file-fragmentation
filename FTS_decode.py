import os
import tarfile

from .fragmented_file import restore_files

source_folder = os.path.abspath(r'a85_input')
output_folder = os.path.abspath(r'a85_output')

if __name__ == '__main__':

    if not os.path.isdir(source_folder):
        assert not os.path.exists(source_folder)
        os.makedirs(source_folder)
        print('source folder <{PATH}> does not exist, creating...'.format(PATH=source_folder))

    if not os.path.isdir(output_folder):
        assert not os.path.exists(output_folder)
        os.makedirs(output_folder)
        print('output folder <{PATH}> does not exist, creating...'.format(PATH=output_folder))

    for temp_archive_path in restore_files(source_folder, output_folder, verbose=True):
        print('restored to <{PATH}>, unpacking archive...'.format(PATH=temp_archive_path))
        with tarfile.open(temp_archive_path, mode='r:gz') as tf:
            tf.extractall(path=output_folder)

        print('unpacked <{PATH}>, deleting archive...'.format(PATH=temp_archive_path))
        os.remove(temp_archive_path)

    print('done!')
