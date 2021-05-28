#!/usr/bin/python
import sys


def setup_ignored(ignored_offsets, start):
    ret = []
    for x in ignored_offsets:
        if x > start:
            x -= start
        ret.extend([x, x + 1, x + 2, x + 3])
    return ret


def file_compare(file1, file2, start1=0, start2=0, compare_len=-1,
                 ignored_offsets=[],
                 max_err=10):
    max_length = compare_len if compare_len > 0 else 0x7FFFFFFF
    with open(file1, 'rb') as f1:
        f1_data = f1.read()
    with open(file2, 'rb') as f2:
        f2_data = f2.read()
    if start1 or start2:
        f1_data = f1_data[start1:]
        f2_data = f2_data[start2:]
    ignore_offsets = setup_ignored(ignored_offsets, start1) if \
        ignored_offsets else ignored_offsets
    max_errs = max_err
    if len(f1_data) != len(f2_data):
        print('Mismatched file lengths: {}, {}'.format(start1 + len(f1_data),
                                                       start2 + len(f2_data)))
    m = min(len(f1_data), len(f2_data), max_length)
    mismatch_file2_offsets = []
    for i in range(m):
        if f1_data[i] != f2_data[i] and i not in ignore_offsets:
            print('Mismatch at {}!\n{}\n{}'.format(i, f1_data[i:i + 5], f2_data[i:i + 5]))
            mismatch_file2_offsets.append(i)
            if len(mismatch_file2_offsets) >= max_errs:
                print('{} errors reached!'.format(max_err))
                break
    if mismatch_file2_offsets:
        print('Differences in "{}" and "{}"'.format(file1, file2))
        print('Target mismatch offsets:\n {}'.format(mismatch_file2_offsets))
    return len(mismatch_file2_offsets) == 0
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
        file1 = '../tmp/cow.brres'
        file2 = '../tmp/original_cow.brres'
    compare_start0 = 0  # 2183680
    compare_start1 = 0  # 2183264
    compare_length = 41000000
    max_err = 10
    ignore_offsets = []
    file_compare(file1, file2, compare_start0, compare_start1, compare_length,
                 ignore_offsets, max_err)
