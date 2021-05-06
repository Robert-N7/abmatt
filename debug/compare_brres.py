import sys

import numpy as np

from abmatt.brres import Brres
from abmatt.brres.lib.binfile import BinFile
from tests import lib


def printCollectionHex(collection):
    st = ""
    i = 0
    for x in collection:
        st += "{0:02X} ".format(x)
        if i % 16 == 15:
            print("{}".format(st))
            st = ""
        i += 1
    print("{}".format(st))


class CompareBins:
    def __init__(self, brres_files, max_err_out=5, ignore_offsets=None, start_at=None, target=None):
        brres1, brres2 = brres_files
        bin1 = BinFile(brres1.name, 'w')
        bin2 = BinFile(brres2.name, 'w')
        if ignore_offsets is None:
            ignore1 = set()
            ignore2 = set()
        else:
            ignore1 = {x for x in ignore_offsets[0]}
            ignore2 = {x for x in ignore_offsets[1]}
        if start_at is None:
            start_at1 = 0
            start_at2 = 0
        else:
            start_at1, start_at2 = start_at
        if target is not None:
            target1, target2 = target
        else:
            target1 = []
            target2 = []
        bin1.target = target1
        bin2.target = target2
        brres1.pack(bin1)
        brres2.pack(bin2)
        ignore1 = self.extend_ignored(ignore1.union({x for x in bin1.linked_offsets}))
        ignore2 = self.extend_ignored(ignore2.union({x for x in bin2.linked_offsets}))
        self.bin1 = bin1
        self.bin2 = bin2
        self.target1 = target1
        self.target2 = target2
        self.brres1 = brres1
        self.brres2 = brres2
        self.ignore1 = ignore1
        self.ignore2 = ignore2
        self.start_at1 = start_at1
        self.start_at2 = start_at2
        self.max_err_out = max_err_out
        self.poly_offset1 = [x[0] for x in bin1.polygon_offsets]
        self.poly_offset2 = [x[0] for x in bin2.polygon_offsets]
        self.poly_names1 = [x[1] for x in bin1.polygon_offsets]
        self.poly_names2 = [x[1] for x in bin2.polygon_offsets]
        self.section_offset1 = [x[0] for x in bin1.section_offsets]
        self.section_offset2 = [x[0] for x in bin2.section_offsets]
        self.section_names1 = [x[1] for x in bin1.section_offsets]
        self.section_names2 = [x[1] for x in bin2.section_offsets]
        self.poly_i = 0
        self.max_poly_i = max(len(self.poly_offset1), len(self.poly_offset2))
        self.section_i = 0
        self.max_section_i = len(self.section_offset1)

    def extend_ignored(self, ignored):
        extended = set()
        for x in ignored:
            extended.add(x)
            extended.add(x + 1)
            extended.add(x + 2)
            extended.add(x + 3)
        return extended

    @staticmethod
    def __get_next_offset(current_i, max_i, offsets1, offsets2, offset1, offset2):
        while current_i < max_i:
            if offsets1[current_i] > offset1 and offsets2[current_i] > offset2:
                return offsets1[current_i], offsets2[current_i], current_i
            current_i += 1
        return None, None, current_i

    def __get_next_poly_offset(self, offset1, offset2):
        next1, next2, self.poly_i = self.__get_next_offset(self.poly_i, self.max_poly_i, self.poly_offset1,
                                                           self.poly_offset2, offset1, offset2)
        return next1, next2

    def __get_next_section_offset(self, offset1, offset2):
        next1, next2, self.section_i = self.__get_next_offset(self.section_i, self.max_section_i, self.section_offset1,
                                                              self.section_offset2, offset1, offset2)
        return next1, next2

    def compare_two_binfiles(self):
        bin1 = self.bin1
        bin2 = self.bin2
        print('Comparing {} and {}'.format(bin1.filename, bin2.filename))
        errs = []
        i1 = self.start_at1
        i2 = self.start_at2
        f1 = bin1.file
        f2 = bin2.file
        poly1, poly2 = self.__get_next_poly_offset(i1, i2)
        section1, section2 = self.__get_next_section_offset(i1, i2)
        while i1 < len(f1) and i2 < len(f2):
            if poly1 is not None and i1 >= poly1:
                if i1 != poly1 or i2 != poly2:
                    i1 = poly1
                    i2 = poly2
                    prev = self.poly_names1[self.poly_i - 1] if self.poly_i > 0 else None
                    print('Re-aligning {}, {} (prev was {})'.format(self.poly_names1[self.poly_i],
                                                                        self.poly_names2[self.poly_i], prev))
                poly1, poly2 = self.__get_next_poly_offset(i1, i2)
            if section1 is not None and i1 >= section1:
                if i1 != section1 or i2 != section2:
                    i1 = section1
                    i2 = section2
                    prev = self.section_names1[self.section_i - 1] if self.section_i > 0 else None
                    print('Re-aligning {}, {} (prev was {})'.format(self.section_names1[self.section_i],
                                                      self.section_names2[self.section_i], prev))
                section1, section2 = self.__get_next_section_offset(i1, i2)
            if i1 not in self.ignore1 and i2 not in self.ignore2 and f1[i1] != f2[i2]:
                errs.append((i1, i2))
                if len(errs) > self.max_err_out:
                    break
                i1 += 4
                i2 += 4
            else:
                i1 += 1
                i2 += 1
        for x in errs:
            i1, i2 = x
            print('      v          @{}, {}'.format(i1, i2))
            printCollectionHex(f1[i1 - 2:i1 + 3])
            printCollectionHex(f2[i2 - 2:i2 + 3])
        np_errs = np.array(errs)
        if len(errs):
            print([list(np_errs[:, 0]), list(np_errs[:, 1])])
        else:
            print('No errors detected')
        return errs


def compare_two_brres(brres1, brres2):
    for i in range(len(brres1.models)):
        mdl1 = brres1.models[i]
        mdl2 = brres2.models[i]
        lib.AbmattTest._test_mats_equal(mdl1.materials, mdl2.materials)
        lib.CheckPositions.model_equal(mdl1, mdl2)


def compare_brres_files(filenames, ignore_offsets=None, start_at=None, target=None):
    if len(filenames) < 1:
        print('Nothing to compare!')
        return
    brres = {}
    for x in filenames:
        brres[x] = Brres(x)
    for i in range(len(filenames) - 1):
        f1 = filenames[i]
        for j in range(i + 1, len(filenames)):
            f2 = filenames[j]
            compare_two_brres(brres[f1], brres[f2])
            CompareBins((brres[f1], brres[f2]),
                        ignore_offsets=ignore_offsets, start_at=start_at, target=target).compare_two_binfiles()


if __name__ == '__main__':
    ignore_offsets = [[], []]
    target = [[910, 911, 9288, 9289, 9290, 9291], [910, 911, 9288, 9289, 9290, 9291]]
    start_at = [0, 0]
    compare_brres_files(sys.argv[1:], ignore_offsets, start_at, target)
