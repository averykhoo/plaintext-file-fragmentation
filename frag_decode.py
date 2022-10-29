import tarfile
import time
from pathlib import Path

from frag_file import defragment_files
from frag_utils import format_seconds

this_folder = Path(__file__).parent
source_folder: Path = this_folder / 'ascii85_encoded'
output_folder: Path = this_folder / 'output_decoded'
password = 'correct 🐎 🔋 staple'  # https://xkcd.com/936/

if __name__ == '__main__':
    # create folder to place plaintext fragment files
    if not source_folder.exists():
        print(f'source folder <{source_folder}> does not exist, creating...')
    source_folder.mkdir(parents=True, exist_ok=True)
    assert source_folder.is_dir()

    # nothing to decode
    if len(list(source_folder.iterdir())) == 0:
        print(f'nothing to decode, place files in <{source_folder}>')

    # start decoding
    else:
        # create output folder if needed
        output_folder.mkdir(parents=True, exist_ok=True)
        assert output_folder.is_dir()

        t = time.time()

        # decode each bunch of fragments separately
        for temp_archive_path in defragment_files(source_folder, password=password, verbose=True):

            # unzip
            print(f'restored to <{temp_archive_path}>, unpacking archive to <{output_folder}>...')
            with tarfile.open(temp_archive_path, mode='r:gz') as tf:
                
                import os
                
                def is_within_directory(directory, target):
                    
                    abs_directory = os.path.abspath(directory)
                    abs_target = os.path.abspath(target)
                
                    prefix = os.path.commonprefix([abs_directory, abs_target])
                    
                    return prefix == abs_directory
                
                def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
                
                    for member in tar.getmembers():
                        member_path = os.path.join(path, member.name)
                        if not is_within_directory(path, member_path):
                            raise Exception("Attempted Path Traversal in Tar File")
                
                    tar.extractall(path, members, numeric_owner=numeric_owner) 
                    
                
                safe_extract(tf, path=output_folder)

            print(f'elapsed: {format_seconds(time.time() - t)}')

            # unpack and remove zip
            print(f'unpacked <{temp_archive_path}>, deleting archive...')
            temp_archive_path.unlink()

            print(f'elapsed: {format_seconds(time.time() - t)}')

    print('done!')
