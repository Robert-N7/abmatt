#!/usr/bin/python
""" Material wii graphics"""
from mdl0.wiigraphics.bp import ColorReg, AlphaFunction, ZMode, BPCommand, BlendMode, ConstantAlpha, IndMatrix


class TevRegister:
    def __init__(self, index, reg_type):
        """ Type, enable for constant color """
        self.reglow = ColorReg(index, 0, reg_type)
        self.reghigh = ColorReg(index, 1, reg_type)
        self.type = reg_type

    def unpack(self, binfile):
        """ unpacks the tev register """
        self.reglow.unpack(binfile)
        self.reghigh.unpack(binfile)
        if not self.type:  # repeats 3x
            binfile.advance(10)

    def pack(self, binfile):
        """ packs the tev register """
        self.reglow.pack(binfile)
        if not self.type:
            self.reghigh.pack(binfile)
            self.reghigh.pack(binfile)
        self.reghigh.pack(binfile)

    def getColor(self):
        """ Gets the color (r,g,b,a) """
        c1 = self.reglow.getColor()
        return c1[1] + self.reghigh.getColor() + c1[0]

    def setColor(self, rgba):
        """ Sets the color (r,g,b,a) """
        self.reglow.setColor(rgba[1:3])
        self.reghigh.setColor((rgba[3], rgba[0]))


class MatGX:
    """ Material graphics codes """

    def __init__(self):
        self.alphafunction = AlphaFunction()
        self.zmode = ZMode()
        self.bpmask = BPCommand(BPCommand.BPMEM_BP_MASK)
        self.blendmode = BlendMode()
        self.constantalpha = ConstantAlpha()
        self.tevRegs = []
        for i in range(3):
            self.tevRegs.append(TevRegister(i + 1, 0))
        self.cctevRegs = []
        for i in range(4):
            self.cctevRegs.append(TevRegister(i, 1))
        self.ras1 = [BPCommand(BPCommand.BPMEM_RAS1_SS0), BPCommand(BPCommand.BPMEM_RAS1_SS1)]
        self.indMatrices = []
        for i in range(3):
            self.indMatrices.append(IndMatrix(i))

    def unpack(self, binfile):
        """ unpacks the mat graphic codes """
        self.alphafunction.unpack(binfile)
        self.zmode.unpack(binfile)
        self.bpmask.unpack(binfile)
        self.blendmode.unpack(binfile)
        self.constantalpha.unpack(binfile)
        binfile.advance(7)  # pad - unknown?
        for i in range(len(self.tevRegs)):
            self.tevRegs[i].unpack(binfile)
        for i in range(len(self.cctevRegs)):
            self.cctevRegs[i].unpack(binfile)
        binfile.align()  # pad
        for x in self.ras1:
            x.unpack(binfile)
        for x in self.indMatrices:
            x.unpack(binfile)
        binfile.align()
        print("BO: {}".format(binfile.offset))
        # should be at layer xf flags

    def pack(self, binfile):
        """ packs the mat graphic codes """
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
        for x in self.ras1:
            x.pack(binfile)
        for x in self.indMatrices:
            x.pack(binfile)
        binfile.align()
