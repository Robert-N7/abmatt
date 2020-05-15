#!/usr/bin/python
#-----------------------------------------------------------------
#   Robert Nelson
# Some useful text
#-----------------------------------------------------------------
import unpack
import brres
from struct import *

class PackBrres:
    def __init__(self, brres):
        self.brres = brres.brres
        self.file = brres.file
        self.filename = brres.filename
        for model in self.brres.models:
            if model.isChanged():
                self.pack_materials(model.mats)
                self.pack_drawlists(model)

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
                if mats[entry[0]].xlu: # xlu mat?
                    newXlu.append(entry)
                else:
                    newOpa.append(entry)
        for i in range(len(drawXlu)):
            # ignore command entries
            if i % 2 != 0:
                entry = drawOpa[i]
                if mats[entry[0]].xlu: # xlu mat?
                    newXlu.append(entry)
                else:
                    newOpa.append(entry)
        newXlu.sort(key = lambda item: item[3]) # sort by draw priority
        newOpa.sort(key = lambda item: item[3])
        # rehook things
        drawlists[1] = newOpa
        drawlists[2] = newXlu
        # the actual byte string and update entry offsets
        data = self.file.file
        offsets = mdl.drawlistsGroup.entryOffsets
        offset = offsets[1] # skip bonetree
        for draw in newOpa:
            pack_into("> B 3H B", data, offset, 4, draw[0], draw[1], draw[2], draw[3])
            offset += 8
        # this offset may change the entry location of xlu draw
        offsets[2] = offset
        for draw in newXlu:
            pack_into("> B 3H B", data, offset, 4, draw[0], draw[1], draw[2], draw[3])
            offset += 8
        mdl.drawlistsGroup.repack(self.file)
