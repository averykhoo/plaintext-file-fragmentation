import os
import tarfile

from fragmented_file import restore_files

this_folder = os.path.abspath(os.path.dirname(__file__))
source_folder = os.path.join(this_folder, r'a85_encoded')
output_folder = os.path.join(this_folder, r'output_decoded')

if __name__ == '__main__':

    if not os.path.isdir(source_folder):
        assert not os.path.exists(source_folder)
        os.makedirs(source_folder)
        print(f'source folder <{source_folder}> does not exist, creating...')

    if not os.path.isdir(output_folder):
        assert not os.path.exists(output_folder)
        os.makedirs(output_folder)
        print(f'output folder <{output_folder}> does not exist, creating...')

    for temp_archive_path in restore_files(source_folder, output_folder, verbose=True):
        print(f'restored to <{temp_archive_path}>, unpacking archive...')
        with tarfile.open(temp_archive_path, mode='r:gz') as tf:
            tf.extractall(path=output_folder)

        print(f'unpacked <{temp_archive_path}>, deleting archive...')
        os.remove(temp_archive_path)

    print('done!')
