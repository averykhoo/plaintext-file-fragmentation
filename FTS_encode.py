import os
import tarfile

from .fragmented_file import fragment_file

source_folder = os.path.abspath(r'raw_input')
output_folder = os.path.abspath(r'a85_encoded')

if __name__ == '__main__':

    do_work = True

    if not os.path.isdir(source_folder):
        assert not os.path.exists(source_folder)
        os.makedirs(source_folder)
        print(f'source folder <{source_folder}> does not exist, creating...')
        do_work = False

    if not os.path.isdir(output_folder):
        assert not os.path.exists(output_folder)
        os.makedirs(output_folder)
        print(f'output folder <{output_folder}> does not exist, creating...')

    if do_work:
        new_archive_name = os.path.basename(source_folder)
        new_archive_path = os.path.abspath(os.path.join(source_folder, new_archive_name + '.tar.gz'))

        if not os.path.exists(new_archive_path):
            print(f'temporarily archiving <{source_folder}> to <{new_archive_path}>')

            with tarfile.open(new_archive_path, mode='w:gz') as tf:
                tf.add(source_folder, arcname=os.path.basename(source_folder))
        else:
            print(f'<{new_archive_path}> already exists, will work on existing file')

        print(f'fragmenting <{new_archive_path}> to <{output_folder}>')
        fragment_paths = fragment_file(new_archive_path, output_folder, max_size=1e6, size_range=5e5, verbose=True)

        print(f'deleting temp archive <{new_archive_path}>')
        os.remove(new_archive_path)

        print(f'created {len(fragment_paths)} fragments')

    print('done!')
