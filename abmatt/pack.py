#!/usr/bin/python
#-----------------------------------------------------------------
#   Robert Nelson
# For packing brres
#-----------------------------------------------------------------
from struct import *

class PackBrres:
    def __init__(self, brres):
        self.brres = brres
        self.file = brres.file
        self.file.convertByteArr()
        self.filename = brres.filename
        for model in brres.models:
            if model.isChanged():
                self.pack_materials(model.mats)
                self.pack_indexGroups(model)
            self.pack_drawlists(model)


    def pack_indexGroups(self, model):
        for group in model.indexGroups:
            if group:
                group.repack(self.file)

    def pack_materials(self, mats):
        for mat in mats:
            mat.pack(self.file)


    def pack_drawlists(self, mdl):
        # Remake drawlists
        drawlists = mdl.drawlists
        drawCmd = 4
        drawOpa = drawlists[1]
        drawXlu = drawlists[2]
        mats = mdl.mats
        newOpa = []
        newXlu = []
        for i in range(len(drawOpa)):
            # ignore command entries
            if i % 2 != 0:
                entry = drawOpa[i]
                matIndex = (entry[0] << 8 | entry[1]) & 0xff
                if mats[matIndex].xlu: # xlu mat?
                    newXlu.append(entry)
                else:
                    newOpa.append(entry)
        for i in range(len(drawXlu)):
            # ignore command entries
            if i % 2 != 0:
                entry = drawXlu[i]
                matIndex = (entry[0] << 8 | entry[1]) & 0xff
                if mats[matIndex].xlu: # xlu mat?
                    newXlu.append(entry)
                else:
                    newOpa.append(entry)
        newXlu.sort(key = lambda item: item[6]) # sort by draw priority
        newOpa.sort(key = lambda item: item[6])
        # print("New Xlu {}".format(newXlu))
        # print("Old xlu {}".format(drawXlu))
        # print("New opa {}".format(newOpa))
        # print("Old opa {}".format(drawOpa))
        # rehook things
        # print("Old length: {} new length {}".format(len(drawlists[1]) + len(drawlists[2]), (len(newOpa) + len(newXlu)) * 2 + 2))
        assert(len(drawlists[1]) + len(drawlists[2]) == (len(newOpa) + len(newXlu)) * 2 + 2)
        # drawlists[1] = newOpa
        # drawlists[2] = newXlu
        # the actual byte string and update entry offsets
        data = self.file.file
        offsets = mdl.drawlistsGroup.entryOffsets
        offset = offsets[1] # skip bonetree
        for draw in newOpa:
            pack_into("> 8B", data, offset, 4, draw[0], draw[1], draw[2], draw[3], draw[4], draw[5], draw[6])
            offset += 8
        pack_into("> B", data, offset, 1)
        offset += 1
        # this offset may change the entry location of xlu draw
        # print("Updating xlu draw offset from {} to {}".format(offsets[2], offset))
        mdl.drawlistsGroup.updateEntryOffset(offset, 2)
        for draw in newXlu:
            pack_into("> 8B", data, offset, 4, draw[0], draw[1], draw[2], draw[3], draw[4], draw[5], draw[6])
            offset += 8
        # print("Data at end of drawlists {}".format(data[offset]))
        pack_into("> B", data, offset, 1) # Terminate, but theoretically should be at same offset now?
