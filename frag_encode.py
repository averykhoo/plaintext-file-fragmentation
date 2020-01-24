import datetime
import tarfile
import time
from pathlib import Path

from frag_file import fragment_file
from frag_utils import format_seconds

this_folder = Path(__file__).parent
source_folder: Path = this_folder / 'input'
archive_folder: Path = this_folder / 'input_archive'
output_folder: Path = this_folder / 'ascii85_encoded'
password = 'correct horse battery staple'  # https://xkcd.com/936/

if __name__ == '__main__':
    # create folder to place input files and folders
    if not source_folder.exists():
        print(f'source folder <{source_folder}> does not exist, creating...')
    source_folder.mkdir(parents=True, exist_ok=True)
    assert source_folder.is_dir()

    # nothing to encode
    if len(list(source_folder.iterdir())) == 0:
        print(f'nothing to encode, place files in <{source_folder}>')

    # start encoding everything
    else:
        # create output folder if needed
        output_folder.mkdir(parents=True, exist_ok=True)
        assert output_folder.is_dir()

        # what to name the archive
        archive_date = datetime.datetime.now().strftime('%Y-%m-%d--%H-%M-%S')
        archive_path = output_folder / f'{archive_date}.tar.gz'

        # should never clash since we're using datetime
        if archive_path.exists():
            print(f'<{archive_path}> already exists, will remove...')
            archive_path.unlink()

        t = time.time()

        # archive everything into a gzip file
        print(f'temporarily archiving <{source_folder}> to <{archive_path}>')
        with tarfile.open(archive_path, mode='w:gz') as tf:
            tf.add(source_folder, arcname=str(archive_date))

        print(f'elapsed: {format_seconds(time.time() - t)} ')

        # plaintext fragmentation (size determined by defaults)
        print(f'fragmenting <{archive_path}> to <{output_folder}>')
        fragment_paths = fragment_file(archive_path, output_folder, password=password, verbose=True)

        print(f'elapsed: {format_seconds(time.time() - t)}')

        # remove gzip file
        print(f'deleting temp archive <{archive_path}>')
        archive_path.unlink()

        # create folder in which to archive the entire input folder
        if not archive_folder.exists():
            print(f'archive folder <{archive_folder}> does not exist, creating...')
        archive_folder.mkdir(parents=True, exist_ok=True)
        assert archive_folder.is_dir()

        # archive input folder, then create new input folder
        source_folder.rename(archive_folder / f'input--{archive_date}')
        source_folder.mkdir(parents=True, exist_ok=True)

        print(f'created {len(fragment_paths)} fragments')
        print(f'elapsed: {format_seconds(time.time() - t)}')

    print('done!')
