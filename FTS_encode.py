import os
import tarfile

from .fragmented_file import fragment_file

source_folder = os.path.abspath(r'temp')
output_folder = os.path.abspath(r'a85_input')

if __name__ == '__main__':

    do_work = True

    if not os.path.isdir(source_folder):
        assert not os.path.exists(source_folder)
        os.makedirs(source_folder)
        print('source folder <{PATH}> does not exist, creating...'.format(PATH=source_folder))
        do_work = False

    if not os.path.isdir(output_folder):
        assert not os.path.exists(output_folder)
        os.makedirs(output_folder)
        print('output folder <{PATH}> does not exist, creating...'.format(PATH=output_folder))

    if do_work:
        new_archive_name = os.path.basename(source_folder)
        new_archive_path = os.path.abspath(os.path.join(source_folder, new_archive_name + '.tar.gz'))

        if not os.path.exists(new_archive_path):
            print('temporarily archiving <{SRC}> to <{OUT}>'.format(SRC=source_folder, OUT=new_archive_path))

            with tarfile.open(new_archive_path, mode='w:gz') as tf:
                tf.add(source_folder, arcname=os.path.basename(source_folder))
        else:
            print('<{OUT}> already exists, will work on existing file'.format(OUT=new_archive_path))

        print('fragmenting <{SRC}> to <{OUT}>'.format(SRC=new_archive_path, OUT=output_folder))
        fragment_paths = fragment_file(new_archive_path, output_folder, max_size=1e6, size_range=5e5, verbose=True)

        print('deleting temp archive <{PATH}>'.format(PATH=new_archive_path))
        os.remove(new_archive_path)

        print('created {N_FRAGS} fragments'.format(N_FRAGS=len(fragment_paths)))

    print('done!')
