from abmatt.lib.binfile import UnpackingError


def unpack_key_frames(key_frame_list, binfile, from_in_place=True, format=None):
    offset = binfile.offset
    if from_in_place:
        binfile.offset = binfile.read('I', 0)[0] + offset
    else:
        binfile.store()
        binfile.recall()
    key_frame_list.entries = []
    # header
    size, uk, fs = binfile.read("2Hf", 8)
    # print('FrameScale: {} i v d'.format(fs))
    # str = ''
    if size <= 0:
        raise UnpackingError(binfile, 'Key frame list has no entries!')
    for i in range(size):
        index, value, delta = binfile.read("3f", 12)
        # str += '({},{},{}), '.format(index, value, delta)
        key_frame_list.entries.append(key_frame_list.KeyFrame(value, index, delta))
    binfile.offset = offset + 4
    return key_frame_list


def unpack_frame_lists(binfile, framelists, exists, isotropic, fixed):
    """
    :param binfile: binfile
    :param framelists: list of frames to unpack
    :param exists: if false, doesn't do anything
    :param isotropic: unpack one frame and set it for all
    :param fixed: list of booleans indicating that the corresponding framelist is a fixed value
    :return: framelists
    """
    if exists:
        if isotropic:
            if fixed[0]:
                fixed_val = binfile.read('f', 4)[0]
                for fl in framelists:
                    fl.set_fixed(fixed_val)
            else:
                fl = unpack_key_frames(framelists[0], binfile, from_in_place=False)
                if len(framelists) > 1:
                    for i in range(1, len(framelists)):
                        framelists[i].paste(fl)
        else:  # deal individually
            for i in range(len(fixed)):
                if fixed[i]:
                    framelists[i].set_fixed(binfile.read('f', 4)[0])
                else:
                    unpack_key_frames(framelists[i], binfile, from_in_place=False)
    return framelists
