import os
import shutil


def archive_create(source_path, archive, overwrite=False):
    archive = os.path.abspath(archive)
    if not overwrite and os.path.exists(archive):
        return
    shutil.make_archive(os.path.basename(archive), 'bztar', root_dir=os.path.dirname(archive), base_dir=source_path)
    return archive+'.tar.bz2'


def archive_extract(archive, into_dir=None):
    if into_dir is None:
        into_dir = os.path.join(os.getcwd(), 'temp')
    shutil.unpack_archive(archive, extract_dir=into_dir, format='bztar')

if __name__ == '__main__':
    archive_create('.','temp')
    archive_extract('temp.tar.bz2')