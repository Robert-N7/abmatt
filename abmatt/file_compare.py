#!/usr/bin/python
import sys


def setup_ignored(ignored_offsets, start):
    ret = []
    for x in ignored_offsets:
        if x > start:
            x -= start
        ret.extend([x, x + 1, x + 2, x + 3])
    return ret


def main(argv):
    if not len(argv) > 1:
        print("Usage: file_compare.py file1 file2")
    print('Comparing "{}" and "{}"'.format(argv[0], argv[1]))
    start = argv[2:4] if len(argv) > 2 else (0, 0)
    max = argv[4] if len(argv) > 4 else 0x7FFFFFFF
    with open(argv[0], 'rb') as f1:
        f1_data = f1.read()
    with open(argv[1], 'rb') as f2:
        f2_data = f2.read()
    if start:
        f1_data = f1_data[start[0]:]
        f2_data = f2_data[start[1]:]
    ignore_offsets = setup_ignored(argv[5], start[0])
    if len(f1_data) != len(f2_data):
        print('Mismatched file lengths: {}, {}'.format(start[0] + len(f1_data), start[1] + len(f2_data)))
    m = min(len(f1_data), len(f2_data), max)
    for i in range(m):
        if f1_data[i] != f2_data[i] and i not in ignore_offsets:
            print('Mismatch at {}!\n{}\n{}'.format(i, f1_data[i:i + 5], f2_data[i:i + 5]))
    # if len(f1_data) > len(f2_data):
    #     print('Extra on {}: {}'.format(argv[0], f1_data[len(f2_data):]))
    # elif len(f2_data) > len(f1_data):
    #     print('Extra data on {}: {}'.format(argv[1], f2_data[len(f1_data):]))


if __name__ == "__main__":
    if len(sys.argv) > 2:
        file1 = sys.argv[0]
        file2 = sys.argv[1]
    else:
        file1 = '../brres_files/beginner_course.brres.pat0'
        file2 = '../brres_files/test.brres.pat0'
    compare_start0 = 0  # 2183680
    compare_start1 = 0  # 2183264
    compare_length = 200
    ignore_offsets = []     # [12, 40]
    main((file1, file2, compare_start0, compare_start1, compare_length, ignore_offsets))
