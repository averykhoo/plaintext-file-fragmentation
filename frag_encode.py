import os
import tarfile

import datetime

from frag_file import fragment_file

this_folder = os.path.abspath(os.path.dirname(__file__))
source_folder = os.path.join(this_folder, r'raw_input')
output_folder = os.path.join(this_folder, r'a85_encoded')

if __name__ == '__main__':
    if not os.path.isdir(source_folder):
        assert not os.path.exists(source_folder)
        os.makedirs(source_folder)
        print('source folder <{}> does not exist, creating...'.format(source_folder))

    if not os.path.isdir(output_folder):
        assert not os.path.exists(output_folder)
        os.makedirs(output_folder)
        print('output folder <{}> does not exist, creating...'.format(output_folder))

    if len(os.listdir(source_folder)) == 0:
        new_archive_name = datetime.datetime.now().strftime('%Y-%m-%d--%H-%M-%S') #os.path.basename(source_folder)
        new_archive_path = os.path.abspath(os.path.join(source_folder, new_archive_name + '.tar.gz'))

        if not os.path.exists(new_archive_path):
            print('temporarily archiving <{}> to <{}>'.format(source_folder,new_archive_path))

            with tarfile.open(new_archive_path, mode='w:gz') as tf:
                tf.add(source_folder, arcname=os.path.basename(source_folder))
        else:
            print('<{}> already exists, will work on existing file'.format(new_archive_path))

        print('fragmenting <{}> to <{}>'.format(new_archive_path,output_folder))
        fragment_paths = fragment_file(new_archive_path, output_folder, max_size=25e6, size_range=5e5, verbose=True)

        print('deleting temp archive <{}>'.format(new_archive_path))
        os.remove(new_archive_path)

        print('created {} fragments'.format(len(fragment_paths)))

    print('done!')
