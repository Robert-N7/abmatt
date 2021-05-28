from copy import deepcopy

from abmatt.lib.matching import validFloat, splitKeyVal


class KeyFrameList:
    """ Representing an animation list
        Always has 1 entry at index 0
    """

    class KeyFrame:
        """ A single animation entry """

        def __init__(self, value, index=0, delta=0):
            self.index = float(index)  # frame index
            self.value = float(value)  # value
            self.delta = float(delta)  # change per frame

        def __eq__(self, other):
            return self.index == other.index and self.value == other.value and self.delta == other.delta

        def __str__(self):
            return '({}:{}:{})'.format(self.index, self.value, self.delta)

    def __init__(self, frameCount, start_value=0):
        self.framecount = frameCount
        self.entries = [self.KeyFrame(start_value)]

    def __len__(self):
        return len(self.entries)

    def __getitem__(self, key):
        key = validFloat(key, 0, self.framecount + .0001)
        return self.get_frame(key)

    def __setitem__(self, key, value):
        key = validFloat(key, 0, self.framecount + .0001)
        if value in ('disabled', 'none', 'remove'):
            self.remove_key_frame(key)
        else:
            delta = None
            if ':' in value:
                value, delta = splitKeyVal(value)
                delta = validFloat(value, -0x7FFFFFFF, 0x7FFFFFFF)
            value = validFloat(value, -0x7FFFFFFF, 0x7FFFFFFF)
            self.set_key_frame(value, key, delta)

    def __eq__(self, other):
        return self.entries == other.entries
        # my_entries = self.entries
        # other_entries = other.entries
        # if len(my_entries) != len(other_entries):
        #     return False
        # for i in range(len(my_entries)):
        #     e = my_entries[i]
        #     o = other_entries[i]
        #     if e.index != o.index or e.value != o.value or e.delta != o.delta:
        #         return False
        # return True

    def __str__(self):
        val = '('
        for x in self.entries:
            val += str(x) + ', '
        return val[:-2] + ')'

    def paste(self, item):
        self.framecount = item.framecount
        self.entries = deepcopy(item.entries)

    def is_default(self, is_scale):
        if len(self.entries) > 1:
            return False
        elif len(self.entries) < 1:
            return True
        return self.entries[0].value == 1 if is_scale else self.entries[0].value == 0

    def is_fixed(self):
        return len(self.entries) == 1  # what about delta?

    def set_fixed(self, value):
        self.entries = [self.KeyFrame(value)]

    def get_frame(self, i):
        """ Gets frame with index i """
        for x in self.entries:
            if x.index == i:
                return x
        return None

    def get_value(self, index=0):
        """ Gets the value of key frame with frame index"""
        for x in self.entries:
            if x.index == index:
                return x.value

    def calc_delta(self, id1, val1, id2, val2):
        if id2 == id1:  # divide by 0
            return self.entries[0].delta
        return (val2 - val1) / (id2 - id1)

    def update_entry(self, entry_index):
        """Calculates the deltas due to a changed entry"""
        entry = self.entries[entry_index]
        if len(self.entries) < 2:  # one or 0
            entry.delta = 0
        else:
            try:
                next = self.entries[entry_index + 1]
                next_id = next.index
            except IndexError:
                next = self.entries[0]
                next_id = next.index + self.framecount
            prev = self.entries[entry_index - 1]
            if entry_index == 0:
                prev_id = prev.index - self.framecount
            else:
                prev_id = prev.index
            entry.delta = self.calc_delta(entry.index, entry.value, next_id, next.value)
            prev.delta = self.calc_delta(prev_id, prev.value, entry.index, entry.value)

    # ------------------------------------------------ Key Frames ---------------------------------------------
    def set_key_frame(self, value, index=0, delta=None):
        """ Adds/sets key frame, overwriting any existing frame at index
            automatically updates delta.
        """
        if not 0 <= index <= self.framecount:
            raise ValueError("Frame Index {} out of range.".format(index))
        entries = self.entries
        entry_index = -1
        cntry = None
        for i in range(len(entries)):
            cntry = entries[i]
            if index < cntry.index:  # insert
                cntry = self.KeyFrame(value, index)
                entries.insert(i, cntry)
                entry_index = i
                break
            elif index == cntry.index:  # replace
                cntry.value = value
                new_entry = cntry
                self.update_entry(i)
                entry_index = i
                break
        if entry_index < 0:  # append it
            cntry = self.KeyFrame(value, index)
            entries.append(cntry)
            self.update_entry(entry_index)
        if delta is None:
            self.update_entry(entry_index)
        else:
            cntry.delta = delta

    def remove_key_frame(self, index):
        """ Removes key frame from list, updating delta """
        if index == 0:
            return
        entries = self.entries
        for i in range(1, len(entries)):
            if entries[i].index == index:
                prev = entries[i - 1]
                if i == len(entries) - 1:  # last entry?
                    next_entry = entries[0]
                    next_id = self.framecount
                else:
                    next_entry = entries[i + 1]
                    next_id = next_entry.index
                prev.value = self.calc_delta(prev.index, prev.value, next_id, next_entry.value)
                entries.pop(i)
                break

    def clear_frames(self, is_scale):
        """ Clears all frames, resetting to one default """
        start_val = 1 if is_scale else 0
        self.entries = [self.KeyFrame(start_val)]

    def set_frame_count(self, frameCount):
        """ Sets frame count, removing extra frames """
        e = self.entries
        self.framecount = frameCount
        for i in range(len(e)):
            if e[i].index > frameCount:
                self.entries = e[:i]  # possibly fix ending delta todo?
                return i
        return 0