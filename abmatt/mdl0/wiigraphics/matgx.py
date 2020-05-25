#!/usr/bin/python
''' Material wii graphics'''
from bp import *

class TevRegister():
    def __init__(self, index, type):
        ''' Type, enable for constant color '''
        reglow = ColorReg(index, 0, type)
        reghigh = ColorReg(index, 1, type)
        self.type = type

    def unpack(self, binfile):
        ''' unpacks the tev register '''
        reglow.unpack(binfile)
        reghigh.unpack(binfile)
        if not self.type:   # repeats 3x
            binfile.advance(10)
    def pack(self, binfile):
        ''' packs the tev register '''
        reglow.pack(binfile)
        if not self.type:
            reghigh.pack(binfile)
            reghigh.pack(binfile)
        reghigh.pack(binfile)

    def getColor(self):
        ''' Gets the color (r,g,b,a) '''
        c1 = reglow.getColor()
        return c1[1] + reghigh.getColor() + c1[0]

    def setColor(self, rgba):
        ''' Sets the color (r,g,b,a) '''
        reglow.setColor(argb[1:3])
        reghigh.setColor(argb[3], rgba[0])


class MatGX():
    ''' Material graphics codes '''
    def __init__(self):
        self.alphafunction = AlphaFunction()
        self.zmode = ZMode()
        self.bpmask = BPCommand(BPCommand.BPMEM_BP_MASK)
        self.blendmode = BlendMode()
        self.constantalpha = ConstantAlpha()
        self.tevRegs = []
        for i in Range(3):
            self.tevRegs.append(TevRegister(i + 1, 0))
        self.cctevRegs = []
        for i in Range(4):
            self.cctevRegs.append(TevRegister(i, 1))

    def unpack(self, binfile):
        ''' unpacks the mat graphic codes '''
        self.alphafunction.unpack(binfile)
        self.zmode.unpack(binfile)
        self.bpmask.unpack(binfile)
        self.blendmode.unpack(binfile)
        self.constantalpha.unpack(binfile)
        binfile.advance(7)  # pad
        for i in range(len(self.tevRegs)):
            self.tevRegs[i].unpack(binfile)
        for i in range(len(self.cctevRegs)):
            self.cctevRegs[i].unpack(binfile)
        binfile.align()  # pad

    def pack(self, binfile):
        ''' packs the mat graphic codes '''
        self.alphafunction.pack(binfile)
        self.zmode.pack(binfile)
        self.bpmask.pack(binfile)
        self.blendmode.pack(binfile)
        self.constantalpha.pack(binfile)
        binfile.advance(7)  # pad
        for i in range(len(self.tevRegs)):
            self.tevRegs[i].pack(binfile)
        for i in range(len(self.cctevRegs)):
            self.cctevRegs[i].pack(binfile)
        binfile.align()

class LayerGX(self, binfile):
