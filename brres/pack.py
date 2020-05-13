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

    def pack_materials(self):
        pass # todo


    def pack_drawlists(self):
        # Remake drawlists
        mdl = self.brres.model
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
        #insert commad byte
        for i in range(len(newOpa)):
            newOpa.insert(i * 2, 4)
        for i in range(len(newXlu)):
            newXlu.insert(i * 2, 4)
        # rehook things
        drawlists[1] = newOpa
        drawlists[2] = newXlu
        # todo, the actual byte string and update entry offsets
