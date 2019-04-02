import datetime
import os
import tarfile

from frag_file import fragment_file

this_folder = os.path.abspath(os.path.dirname(__file__))
source_folder = os.path.join(this_folder, r'input')
output_folder = os.path.join(this_folder, r'ascii85_encoded')

if __name__ == '__main__':
    if not os.path.isdir(source_folder):
        assert not os.path.exists(source_folder)
        os.makedirs(source_folder)
        print('source folder <{}> does not exist, creating...'.format(source_folder))

    if len(os.listdir(source_folder)) == 0:
        print('nothing to encode, place files in <{}>'.format(source_folder))

    else:
        if not os.path.isdir(output_folder):
            assert not os.path.exists(output_folder)
            os.makedirs(output_folder)
            print('output folder <{}> does not exist, creating...'.format(output_folder))

        temp_archive_name = datetime.datetime.now().strftime('%Y-%m-%d--%H-%M-%S')
        temp_archive_path = os.path.abspath(os.path.join(output_folder, temp_archive_name + '.tar.gz'))

        if os.path.exists(temp_archive_path):
            print('<{}> already exists, will work on existing file'.format(temp_archive_path))

        else:
            print('temporarily archiving <{}> to <{}>'.format(source_folder, temp_archive_path))
            with tarfile.open(temp_archive_path, mode='w:gz') as tf:
                tf.add(source_folder, arcname=temp_archive_name)

        print('fragmenting <{}> to <{}>'.format(temp_archive_path, output_folder))
        fragment_paths = fragment_file(temp_archive_path, output_folder, verbose=True)

        print('deleting temp archive <{}>'.format(temp_archive_path))
        os.remove(temp_archive_path)

        print('created {} fragments'.format(len(fragment_paths)))

    print('done!')
