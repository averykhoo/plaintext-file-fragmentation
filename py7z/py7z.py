import os
import subprocess
import sys

__author__ = 'Avery'

SYS_BITS = sys.maxsize.bit_length() + 1
EXE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), u'7-zip/x%d/7z.exe' % SYS_BITS))
assert SYS_BITS in (32, 64)
assert os.path.exists(EXE_PATH)


def archive_create(files_and_folders, archive, password=None, encrypt_headers=False, overwrite=False):
    """
    create 7z archive from some files and folders
    files and folders will be placed in the root of the archive

    :param files_and_folders: list of paths
    :param archive: path (or name)
    :param password: ascii only, excluding null bytes and double-quote char
    :param encrypt_headers: encrypt file names and directory tree within the archive
    :return: output printed by 7zip
    """

    # make paths absolute and unicode
    archive_path = os.path.abspath(unicode(archive))
    todo_paths = [os.path.abspath(unicode(item)) for item in files_and_folders]

    # check validity of input files and folders
    seen = {}
    for file_path in files_and_folders:
        file_name = os.path.basename(file_path)
        assert file_name not in seen, \
            u'multiple items with same filename added to archive: <{PATH1}> and <{PATH2}>)' \
                .format(NAME=file_name, PATH1=seen[file_name], PATH2=file_path)
        seen[file_name] = file_path

    # 7z will not create an archive over an existing dir
    assert not os.path.isdir(archive_path), u'dir already exists at output path'

    # don't want to overwrite anything
    assert overwrite or not os.path.isfile(archive_path), u'file already exists at output path'

    # base command (without input files/folders)
    command = [EXE_PATH,
               u'a',
               u'-t7z',
               u'-m0=lzma2',
               u'-mx=9',
               archive_path]

    # -t7z         -- type of archive             -> 7z
    # -m0=lzma2    -- compression algorithm       -> lzma2
    # -mx=9        -- compression level           -> 9 = ultra
    # -aoa         -- duplicate destination files -> oa = overwrite all
    # -mfb=64      -- fast bytes                  -> what is this
    # -md=32m      -- dictionary size?            -> 32Mb
    # -ms=on       -- solid                       -> yes (default)
    # -d=64m       -- dictionary size             -> 66Mb
    # -mhe         -- encrypt header              -> default off
    # -p{PASSWORD} -- set password = "{PASSWORD}" -> default unencrypted

    # add password and header encryption
    if password is not None:
        assert len(password) > 0, u'password must be at least one character long'

        # need to write and run batch file to use this char
        if u'"' in password:
            raise NotImplementedError(u'double-quote not supported')

        # command += u' "-p{PASSWORD}"'.format(PASSWORD=password)
        command += [u'-p{PASSWORD}'.format(PASSWORD=password)]
        if encrypt_headers:
            command += [u'-mhe']

    # add files
    command += todo_paths

    # make the file, check that it's okay
    ret_val = subprocess.check_output(command)
    assert u'Everything is Ok' in ret_val, u'something went wrong: ' + ret_val

    # todo: parse ret_val into something useful
    return ret_val


def archive_test(archive, password=None):
    """
    test the integrity of an archive

    :param archive: path (or name)
    :param password: ascii only, excluding null bytes and double-quote char
    :return: output printed by 7zip
    """
    # todo: make unicode friendly
    archive_path = os.path.abspath(unicode(archive))

    # set arbitrary password if none given
    if password is None:
        password = u'\x7f'  # ascii for DEL key

    # validity of provided password (if any)
    assert len(password) > 0, u'password must be at least one character long'

    # need to write and run batch file to use this char
    if u'"' in password:
        raise NotImplementedError(u'double-quote not supported')

    # always supply a password
    command = [EXE_PATH,
               u't',
               u'-p{PASSWORD}'.format(PASSWORD=password),
               archive_path]

    # make the file, check that it's okay
    ret_val = subprocess.check_output(command)
    assert u'Everything is Ok' in ret_val, u'something went wrong: ' + ret_val

    # todo: parse ret_val into something useful
    return ret_val


def archive_extract(archive, into_dir=None, password=None, flat=False):
    archive_path = os.path.abspath(unicode(archive))
    assert os.path.isfile(archive_path), u'archive does not exist at provided path'

    # set arbitrary password if none given
    if password is None:
        password = u'\x7f'  # ascii for DEL key

    # validity of provided password (if any)
    assert len(password) > 0, u'password must be at least one character long'

    # set arbitrary password if none given
    if into_dir is None:
        into_dir = u'.'  # this directory

    # validity of provided dirname (if any)
    into_dir = os.path.abspath(into_dir.strip())
    assert len(into_dir) > 0, u'containing dir name must be at least one character long'
    assert all(char not in os.path.basename(into_dir) for char in u'\\/:*?"<>|'), u'invalid dir name'
    assert not os.path.isfile(into_dir), u'dir already exists at output path, cannot create folder'

    # need to write and run batch file to use this char
    if u'"' in password:
        raise NotImplementedError(u'double-quote not supported')

    # make command
    command = [EXE_PATH,
               u'xe'[flat],  # decide which flag to use
               u'-o{DIR}'.format(DIR=into_dir),
               u'-p{PASSWORD}'.format(PASSWORD=password),
               archive_path]

    # make the file, check that it's okay
    ret_val = subprocess.check_output(command)
    assert u'Everything is Ok' in ret_val, u'something went wrong: ' + ret_val

    # todo: parse ret_val into something useful
    return ret_val


if __name__ == '__main__':
    # cleanup
    if os.path.exists(ur'passwd.7z'):
        os.remove(ur'passwd.7z')
    # test: create archive
    archive_create([ur'cmds.txt', ur'__init__.py'],
                   ur'passwd.7z',
                   password=('passwd'),
                   encrypt_headers=True
                   )
    # test: test archive
    archive_test(r'passwd.7z',
                 password='passwd')
    # test: extract archive
    archive_extract(r'passwd.7z',
                    into_dir=r'passwd',
                    password='passwd')
    # cleanup
    os.remove(r'passwd.7z')
