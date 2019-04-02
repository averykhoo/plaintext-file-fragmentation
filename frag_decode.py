import os
import tarfile

from frag_file import restore_files

this_folder = os.path.abspath(os.path.dirname(__file__))
source_folder = os.path.join(this_folder, r'ascii85_encoded')
output_folder = os.path.join(this_folder, r'output_decoded')

if __name__ == '__main__':

    if not os.path.isdir(source_folder):
        assert not os.path.exists(source_folder)
        os.makedirs(source_folder)
        print('source folder <{}> does not exist, creating...'.format(source_folder))

    if not os.path.isdir(output_folder):
        assert not os.path.exists(output_folder)
        os.makedirs(output_folder)
        print('output folder <{}> does not exist, creating...'.format(output_folder))

    for temp_archive_path in restore_files(source_folder, verbose=True):
        if temp_archive_path is None:
            continue
        print('restored to <{}>, unpacking archive...'.format(temp_archive_path))
        with tarfile.open(temp_archive_path, mode='r:gz') as tf:
            tf.extractall(path=output_folder)

        print('unpacked <{}>, deleting archive...'.format(temp_archive_path))
        os.remove(temp_archive_path)

    print('done!')
