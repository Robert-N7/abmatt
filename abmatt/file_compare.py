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
    mismatch_file2_offsets = []
    for i in range(m):
        if f1_data[i] != f2_data[i] and i not in ignore_offsets:
            print('Mismatch at {}!\n{}\n{}'.format(i, f1_data[i:i + 5], f2_data[i:i + 5]))
            mismatch_file2_offsets.append(i)
    print('Target mismatch offsets:\n {}'.format(mismatch_file2_offsets))
    # if len(f1_data) > len(f2_data):
    #     print('Extra on {}: {}'.format(argv[0], f1_data[len(f2_data):]))
    # elif len(f2_data) > len(f1_data):
    #     print('Extra data on {}: {}'.format(argv[1], f2_data[len(f1_data):]))


if __name__ == "__main__":
    if len(sys.argv) > 2:
        file1 = sys.argv[0]
        file2 = sys.argv[1]
    else:
        file1 = 'C:/Users/rober/Desktop/candyland/course_model_0.7.4.brres'
        file2 = '../brres_files/test.brres'
    compare_start0 = 0  # 2183680
    compare_start1 = 0  # 2183264
    compare_length = 18300
    ignore_offsets = [40, 96, 136, 452, 508, 548, 732, 916, 1100, 1284, 1468, 1652, 56, 72, 112, 360, 524, 2008, 152, 1260, 1444, 1796, 15688, 16728, 57876, 168, 1180, 1364, 1716, 8168, 9208, 63380, 184, 1244, 1428, 1780, 14184, 15224, 107092, 200, 1228, 1412, 1764, 12680, 13720, 150804, 216, 1148, 1332, 1684, 5160, 6200, 153588, 232, 1164, 1348, 1700, 6664, 7704, 154324, 248, 1132, 1316, 1668, 3656, 4696, 241684, 264, 1212, 1396, 1748, 11176, 12216, 329044, 280, 1196, 1380, 1732, 9672, 10712, 503700, 468, 484, 564, 748, 1484, 22360, 35852, 46700, 580, 764, 1500, 22840, 36204, 46764, 596, 780, 1516, 25016, 38188, 47212, 612, 796, 1532, 25400, 38348, 47276, 628, 812, 1548, 25784, 38476, 47340, 644, 828, 1564, 26520, 39276, 47628, 660, 844, 1580, 31512, 42284, 49388, 676, 860, 1596, 32248, 43116, 49484, 692, 876, 1612, 32760, 43596, 49548, 708, 892, 1628, 33720, 44844, 49612, 932, 50060, 948, 50316, 964, 51788, 980, 51884, 996, 51980, 1012, 52364, 1028, 55436, 1044, 55788, 1060, 56012, 1076, 56492, 1116, 1300, 2216, 32, 36, 44, 48, 52, 64, 68, 88, 92, 100, 104, 108, 116, 128, 132, 140, 144, 148, 156, 160, 164, 172, 176, 180, 188, 192, 196, 204, 208, 212, 220, 224, 228, 236, 240, 244, 252, 256, 260, 268, 272, 276, 284, 304, 308, 312, 316, 320, 324, 328, 332, 336, 340, 344, 348, 352, 356, 400, 444, 448, 456, 460, 464, 472, 476, 480, 488, 500, 504, 512, 516, 520, 528, 540, 544, 552, 556, 560, 568, 572, 576, 584, 588, 592, 600, 604, 608, 616, 620, 624, 632, 636, 640, 648, 652, 656, 664, 668, 672, 680, 684, 688, 696, 700, 704, 712, 724, 728, 736, 740, 744, 752, 756, 760, 768, 772, 776, 784, 788, 792, 800, 804, 808, 816, 820, 824, 832, 836, 840, 848, 852, 856, 864, 868, 872, 880, 884, 888, 896, 908, 912, 920, 924, 928, 936, 940, 944, 952, 956, 960, 968, 972, 976, 984, 988, 992, 1000, 1004, 1008, 1016, 1020, 1024, 1032, 1036, 1040, 1048, 1052, 1056, 1064, 1068, 1072, 1080, 1092, 1096, 1104, 1108, 1112, 1120, 1124, 1128, 1136, 1140, 1144, 1152, 1156, 1160, 1168, 1172, 1176, 1184, 1188, 1192, 1200, 1204, 1208, 1216, 1220, 1224, 1232, 1236, 1240, 1248, 1252, 1256, 1264, 1276, 1280, 1288, 1292, 1296, 1304, 1308, 1312, 1320, 1324, 1328, 1336, 1340, 1344, 1352, 1356, 1360, 1368, 1372, 1376, 1384, 1388, 1392, 1400, 1404, 1408, 1416, 1420, 1424, 1432, 1436, 1440, 1448, 1460, 1464, 1472, 1476, 1480, 1488, 1492, 1496, 1504, 1508, 1512, 1520, 1524, 1528, 1536, 1540, 1544, 1552, 1556, 1560, 1568, 1572, 1576, 1584, 1588, 1592, 1600, 1604, 1608, 1616, 1620, 1624, 1632, 1644, 1648, 1656, 1660, 1664, 1672, 1676, 1680, 1688, 1692, 1696, 1704, 1708, 1712, 1720, 1724, 1728, 1736, 1740, 1744, 1752, 1756, 1760, 1768, 1772, 1776, 1784, 1788, 1792, 1800, 1808, 1812, 1820, 1824, 1832, 1836, 1844, 1848, 1856, 1860, 1868, 1872, 1880, 1884, 1892, 1896, 1904, 1908, 2096, 2100, 2248, 2256, 2268, 3688, 3696, 3708, 5192, 5200, 5212, 6696, 6704, 6716, 8200, 8208, 8220, 9704, 9712, 9724, 11208, 11216, 11228, 12712, 12720, 12732, 14216, 14224, 14236, 15720, 15728, 15740, 22404, 22884, 25060, 25444, 25828, 26564, 31556, 32292, 32804, 33764, 35848, 36200, 38184, 38344, 38472, 39272, 42280, 43112, 43592, 44840, 46696, 46760, 47208, 47272, 47336, 47624, 49384, 49480, 49544, 49608, 50056, 50312, 51784, 51880, 51976, 52360, 55432, 55784, 56008, 56488, 57872, 63376, 107088, 150800, 153584, 154320, 241680, 329040, 503696]
    main((file1, file2, compare_start0, compare_start1, compare_length, ignore_offsets))
