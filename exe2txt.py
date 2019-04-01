import fnmatch
import os
import subprocess


def crawl(top, file_pattern='*'):
    """generator giving all file paths"""
    for root_path, dir_list, file_list in os.walk(top):
        for file_name in fnmatch.filter(file_list, file_pattern):
            yield os.path.join(root_path, file_name)


def encode(input_filename, lines_per_file=-1, out_folder='b64.txt'):
    assert os.path.isfile(input_filename), 'file does not exist'
    # assert lines_per_file > 0
    assert lines_per_file < 100000  # lotus notes starts to lag and act weird
    assert out_folder

    file_path = os.path.abspath(input_filename)
    out_path = os.path.join(os.path.dirname(file_path), out_folder)
    command = 'certutil -encode -v -f %s %s' % (file_path, out_path)

    try:
        print(subprocess.check_output(command, shell=False))
    except subprocess.CalledProcessError:
        raise

        # lines = [line for line in open('b64.out')]
        # if lines_per_file > 0:
        #     zeroes = math.ceil(math.log10(math.ceil(float(len(lines)) / lines_per_file)))
        # else:
        #     zeroes = 0
        #     lines_per_file = 99999999
        # i = 0
        # if not os.path.isdir(out_path):
        #     os.makedirs(out_path)
        #
        # while lines:
        #     i += 1
        #     file_to_write = '%s\\%s-%s%sd.txt' % (out_folder, os.path.basename(file_path), '%', '0%d' % zeroes) % i
        #     # file_to_write = 'out\%s-%04d.txt' % (filename, i)
        #     with open(file_to_write, 'w') as f:
        #         for _ in xrange(lines_per_file):
        #             try:
        #                 f.write(lines.pop(0))
        #             except:
        #                 break
        #     print file_to_write
        #
        # os.remove('b64.out')


if __name__ == '__main__':
    for path in crawl('.', '*.7z'):
        print(path)
        encode(path)
        break
