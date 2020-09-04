#!/usr/bin/python
import math
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
    start = argv[2] if len(argv) > 2 else 0
    max = argv[3] if len(argv) > 3 else 0x7FFFFFFF
    with open(argv[0], 'rb') as f1:
        f1_data = f1.read()
    with open(argv[1], 'rb') as f2:
        f2_data = f2.read()
    if start:
        f1_data = f1_data[start:]
        f2_data = f2_data[start:]
    ignore_offsets = setup_ignored(argv[4], start)
    if len(f1_data) != len(f2_data):
        print('Mismatched file lengths: {}, {}'.format(start + len(f1_data), start + len(f2_data)))
    m = min(len(f1_data), len(f2_data), max)
    for i in range(m):
        if f1_data[i] != f2_data[i] and i not in ignore_offsets:
            print('Mismatch at {}!\n{}\n{}'.format(start + i, f1_data[i:i + 5], f2_data[i:i + 5]))
    # if len(f1_data) > len(f2_data):
    #     print('Extra on {}: {}'.format(argv[0], f1_data[len(f2_data):]))
    # elif len(f2_data) > len(f1_data):
    #     print('Extra data on {}: {}'.format(argv[1], f2_data[len(f1_data):]))


if __name__ == "__main__":
    if len(sys.argv) > 2:
        file1 = sys.argv[0]
        file2 = sys.argv[1]
    else:
        file1 = '../test_files/cow_no_anim.brres'
        file2 = '../test_files/test.brres'
    compare_start = 0
    compare_length = 1000000
    ignore_offsets = [910, 911, 40, 96, 152, 356, 412, 452, 492, 532, 572, 612, 4112, 4168, 4384, 4424, 4464, 4504, 4544, 4584, 4624, 4664, 56, 72, 112, 264, 128, 3976, 168, 4680, 8316, 25684, 372, 4128, 388, 4144, 428, 660, 468, 508, 3468, 3788, 548, 588, 868, 628, 2872, 4640, 9336, 4184, 4780, 4200, 4988, 4216, 5196, 4232, 5404, 4248, 5612, 4264, 5820, 4280, 6028, 4296, 6236, 4312, 6444, 4328, 6652, 4344, 6860, 4360, 7068, 4400, 4440, 4480, 16684, 20236, 21996, 4520, 22668, 4560, 4600, 7276]
    main((file1, file2, compare_start, compare_length, ignore_offsets))
