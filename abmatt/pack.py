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
                self.pack_Folders(model)
            self.pack_drawlists(model)


    def pack_Folders(self, model):
        for group in model.Folders:
            if group:
                group.repack(self.file)

    def pack_materials(self, mats):
        for mat in mats:
            mat.pack(self.file)


    def pack_drawlists(self, mdl):
        # Remake drawlists - possible that list doesn't exist?
        drawCmd = 4
        lists = mdl.drawlists
        opaIndex = -1
        xluIndex = -1
        for i in range(len(lists)):
            if lists[i].name == "DrawOpa":
                opaIndex = i
                drawOpa = lists[i].cmds
            elif lists[i].name == "DrawXlu":
                xluIndex = i
                drawXlu = lists[i].cmds
        if opaIndex == -1 or xluIndex == -1:
            print("Warning, unable to remake drawlists for model {}.".format(mdl.name))
            return False
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
        for i in range(len(lists[xluIndex])):
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
        # rehook things
        # assert(len(drawOpa) + len(drawXlu) == (len(newOpa) + len(newXlu)) * 2 + 2)
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
