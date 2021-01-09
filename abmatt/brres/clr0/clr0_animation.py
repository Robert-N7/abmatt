class Clr0Animation:

    def __init__(self, name, framecount=1, loop=True):
        self.name = name
        self.framecount = framecount
        self.loop=loop
        self.flags = [False] * 16
        self.is_constant = [False] * 16
        self.entry_masks = []
        self.entries = []   # can be fixed (if constant) otherwise key frame list
