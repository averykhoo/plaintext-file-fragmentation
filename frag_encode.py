import datetime
import os
import tarfile
import time

from frag_file import fragment_file

this_folder = os.path.abspath(os.path.dirname(__file__))
source_folder = os.path.join(this_folder, r'input')
output_folder = os.path.join(this_folder, r'ascii85_encoded')

if __name__ == '__main__':
    # create folder to place input files and folders
    if not os.path.isdir(source_folder):
        assert not os.path.exists(source_folder)
        os.makedirs(source_folder)
        print('source folder <{}> does not exist, creating...'.format(source_folder))

    # nothing to encode
    if len(os.listdir(source_folder)) == 0:
        print('nothing to encode, place files in <{}>'.format(source_folder))

    # start encoding everything
    else:
        if not os.path.isdir(output_folder):
            assert not os.path.exists(output_folder)
            os.makedirs(output_folder)
            print('output folder <{}> does not exist, creating...'.format(output_folder))

        # what to name the archive
        archive_name = datetime.datetime.now().strftime('%Y-%m-%d--%H-%M-%S')
        archive_path = os.path.abspath(os.path.join(output_folder, archive_name + '.tar.gz'))

        # should never clash since we're using datetime
        if os.path.exists(archive_path):
            print('<{}> already exists, will remove...'.format(archive_path))
            os.remove(archive_path)

        t = time.time()

        # archive everything into a gzip file
        print('temporarily archiving <{}> to <{}>'.format(source_folder, archive_path))
        with tarfile.open(archive_path, mode='w:gz') as tf:
            tf.add(source_folder, arcname=archive_name)

        print(f'elapsed: {time.time() - t} seconds')

        # plaintext fragmentation (size determined by defaults)
        print('fragmenting <{}> to <{}>'.format(archive_path, output_folder))
        fragment_paths = fragment_file(archive_path, output_folder, password='password', verbose=True)

        print(f'elapsed: {time.time() - t} seconds')

        # remove gzip file, archive input folder
        print('deleting temp archive <{}>'.format(archive_path))
        os.remove(archive_path)
        os.rename(source_folder, source_folder + '--' + archive_name)

        os.makedirs(source_folder)

        print('created {} fragments'.format(len(fragment_paths)))

        print(f'elapsed: {time.time() - t} seconds')

    print('done!')
