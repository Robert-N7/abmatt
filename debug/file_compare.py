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
    max_length = argv[4] if len(argv) > 4 else 0x7FFFFFFF
    with open(argv[0], 'rb') as f1:
        f1_data = f1.read()
    with open(argv[1], 'rb') as f2:
        f2_data = f2.read()
    if start:
        f1_data = f1_data[start[0]:]
        f2_data = f2_data[start[1]:]
    ignore_offsets = setup_ignored(argv[5], start[0]) if len(argv) > 5 else []
    max_errs = argv[6] if len(argv) > 6 else 20
    if len(f1_data) != len(f2_data):
        print('Mismatched file lengths: {}, {}'.format(start[0] + len(f1_data), start[1] + len(f2_data)))
    m = min(len(f1_data), len(f2_data), max_length)
    mismatch_file2_offsets = []
    for i in range(m):
        if f1_data[i] != f2_data[i] and i not in ignore_offsets:
            print('Mismatch at {}!\n{}\n{}'.format(i, f1_data[i:i + 5], f2_data[i:i + 5]))
            mismatch_file2_offsets.append(i)
            if len(mismatch_file2_offsets) >= max_errs:
                print('{} errors reached!'.format(max_err))
                break
    print('Target mismatch offsets:\n {}'.format(mismatch_file2_offsets))
    # if len(f1_data) > len(f2_data):
    #     print('Extra on {}: {}'.format(argv[0], f1_data[len(f2_data):]))
    # elif len(f2_data) > len(f1_data):
    #     print('Extra data on {}: {}'.format(argv[1], f2_data[len(f1_data):]))


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) >= 2:
        file1 = args[0]
        file2 = args[1]
    else:
        file1 = '../brres_files/beginner_course.brres'
        file2 = '../brres_files/test.brres'
    compare_start0 = 0  # 2183680
    compare_start1 = 0  # 2183264
    compare_length = 41000000
    max_err = 10
    ignore_offsets = []
    main((file1, file2, compare_start0, compare_start1, compare_length, ignore_offsets, max_err))
