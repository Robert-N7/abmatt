#!/usr/bin/python
''' binary file read/writing operations '''
from struct import *

# -------------------------------------------------------------------------------
class BinFile:
    ''' BinFile class: for packing and unpacking binfileary files'''
    def __init__(self, filename, bom='>', mode='r'):
        '''
        filename:   name of file to read/write
        bom:    byte order mark (>|<) Big endian or little endian
        mode:   (r|w)
        len:    initial length of file (write only)
        '''
        self.offset = 0
        self.stack = [] # used for tracking depth in files
        self.references = {}    # used for forward references in relation to start
        self.bom  = bom     # byte order mark > | <
        self.nameRefMap = {}    # for packing name references
        self.lenMap = {}      # used for tracking length of files
        self.isWriteMode = (mode == 'w')
        if not self.isWriteMode:
            file = open(filename, "rb")
            self.file = file.read()
            file.close()
        else:
            self.filename = filename
            self.file = bytearray()
        self.start()

    def commitWrite(self):
        ''' writes the file '''
        with open(self.filename, "wb") as f:
            f.write(self.file)

    def align(self, alignment = 0x20):
        ''' Aligns to the alignment relative to file start '''
        pastAlign = (self.offset - self.beginOffset) % alignment
        if pastAlign:
            self.advance(alignment - pastAlign)

    # start / marks offset which pointers are based
    def start(self):
        ''' Starts reading a file, remembering the offset '''
        self.beginOffset = self.offset
        self.stack.append(self.offset)
        self.refMarker = []
        self.references[self.beginOffset] = self.refMarker

    #  end / pops last start offset off stack
    def end(self):
        # write file length?
        if self.isWriteMode:
            lenOffset = self.lenMap.get(self.beginOffset)
            if lenOffset:
                self.writeOffset("I", lenOffset + self.beginOffset, self.offset - self.beginOffset)
        self.stack.pop()
        self.beginOffset = self.stack[-1]
        self.refMarker = self.references[self.beginOffset]

    def markLen(self):
        ''' Marks the current offset as length of file,
            which gets filled in by binfile.end in write mode
        '''
        self.lenMap[self.beginOffset] = self.offset
        if not self.isWriteMode:
            return self.read("I", 4)
        else:
            if self.offset == len(self.file):
                self.file.extend(b'\0' * 4)
            self.offset += 4

    # Writing back ptrs, use mark and createref together, write mode
    def mark(self, numRefs=1):
        ''' Marks the current offset(s) relative to start as storage for ptrs,
            advancing the file offset
            Use in write mode with createRef
        '''
        li = self.refMarker
        for i in range(numRefs):
            li.append(file.offset - self.beginOffset)
        self.advance(4 * numRefs)

    def createRefFromStored(self, refIndex = 0, pop = True):
        ''' Creates reference to the current file offset
            in relation to the stored offset (not start!)
        '''
        try:
            if pop:
                markedOffset = self.refMarker.pop(refIndex)
            else:
                markedOffset = self.refMarker[refIndex]
            self.writeOffset("I", markedOffset, self.offset - markedOffset)
            return markedOffset
        except:
            raise("Marked index from {} at {} does not exist!".format(self.beginOffset, refIndex))

    def createRef(self, refIndex = 0, pop = True):
        '''
         Creates a reference to the current file offset
         using the reference marked at refIndex relative to start
         pops and returns the marked offset
        '''
        try:
            if pop:
                markedOffset = self.refMarker.pop(refIndex)
            else:
                markedOffset = self.refMarker[refIndex]
            self.writeOffset("I", markedOffset, self.offset - self.beginOffset)
            return markedOffset
        except:
            raise("Marked index from {} at {} does not exist!".format(self.beginOffset, refIndex))

    def createParentRef(self, refIndex = 0, pop = True):
        ''' Creates a reference from parent marked offset'''
        return self.createRefFrom(self.getParentOffset(), refIndex, pop)

    def createRefFrom(self, startRef, index = 0, pop = True):
        ''' Creates ref by getting marked offset, indexing from startRef, at the index '''
        try:
            refs = self.references[startRef]
            if pop:
                markedOffset = refs.pop(index)
            else:
                markedOffset = refs[index]
            self.writeOffset("I", markedOffset, self.offset - startRef)
            return markedOffset
        except:
            raise("Marked index from {} at {} does not exist!".format(startRef, index))

    # Storing and recalling forward pointers - read mode
    def pushCurrentOffset(self):
        ''' pushes current offset to come back to with recall in ref from start'''
        offset = self.offset - self.beginOffset
        self.refMarker.append(offset)

    def bl_unpack(self, obj, fromStart=True):
        '''reads offset and unpacks object '''
        off = self.read("I", 4)
        offset = self.offset
        self.offset = self.beginOffset + off[0] if fromStart else offset + off
        obj.unpack(self)
        self.offset = offset
        return obj

    def store(self, numRefs = 1):
        ''' Reads and stores a pointer relative to start
            Use in read mode with recallAndPop
        '''
        refs = self.read("I" * numRefs, numRefs * 4)
        ret = len(self.refMarker)
        self.refMarker.extend(list(refs))
        return ret

    def recall(self, index = 0, pop = True):
        '''
            Recalls a reference, advancing to it
            returns the reference offset relative to start
        '''
        try:
            if pop:
                offset = self.refMarker.pop(index)
            else:
                offset = self.refMarker[index]
            self.offset = offset + self.beginOffset
            return offset
        except:
            raise ValueError("Stored index from {} at {} does not exist!".format(self.beginOffset, index))

    def recallParent(self, index = 0, pop = True):
        ''' Recalls reference from parent
            returns offset in relation to current start
        '''
        return self.recallOffset(self.getParentOffset(), index, pop)

    def recallOffset(self, startOffset, index = 0, pop = True):
        ''' recalls reference at specific offset '''
        # possible error if out of range startoffset or index
        try:
            refs = self.references[startOffset]
            if pop:
                offset = refs.pop(index)
            else:
                offset = refs[index]
            self.offset = offset + startOffset
            return offset
        except:
            raise("Stored index from {} at {} does not exist!".format(startOffset, index))

    def recallAll(self):
        ''' retrieves all refs at current start, removing them '''
        refs = self.refMarker
        self.references[self.beginOffset] = self.refMarker = []
        return refs


    # advance
    def advance(self, step):
        ''' advances offset pointer, possibly padding with 0's in write mode '''
        self.offset += step
        if self.isWriteMode:
            m = file.offset - len(self.file)
            if m > 0:
                self.file.extend(b'\0' * m)

    def getParentOffset(self):
        ''' Gets the parent offset off the stack'''
        l = len(self.stack)
        if l > 1:
            return self.stack[l - 2]
        else:
            return 0

    # get outer (file/container) offset
    def getOuterOffset(self):
        ''' Gets the negative offset to the outer file in relation to current start'''
        len = len(self.stack)
        if len > 1:
            return self.stack[len - 2] - self.beginOffset
        else:
            return 0

    # Reading / unpacking
    def readMagic(self, advance = True):
        ''' reads the magic from this file, optionally advancing '''
        magic = unpack_from(self.bom + "4s", self.file, self.offset)
        if advance:
            self.offset += 4
        return magic[0]

    def read(self, fmt, len):
        read = unpack_from(self.bom + fmt, self.file, self.offset)
        self.offset += len
        return read

    def readOffset(self, fmt, offset): # len not needed
        return unpack_from(self.bom + fmt, self.file, offset)

    def readRemaining(self, filelen):
        ''' Reads and returns remaining data as bytes '''
        remainder = filelen - (self.offset - self.beginOffset)
        return self.read("{}B".format(remainder), remainder)

    # Writing/packing
    def writeMagic(self, magic):
        self.write("4s", magic)

    def write(self, fmt, args):
        ''' Packs data onto end of file, shifting the offset'''
        self.file.extend(pack(self.bom + fmt, self.file, args))
        self.offset = len(self.file)
        return len


    def writeOffset(self, fmt, offset, args):
        ''' packs data at offset, must be less than file length '''
        # possible todo... automatically extend if it exceeds length
        pack_into(self.bom + fmt, self.file, offset, args)
        return len

    def writeRemaining(self, bytes):
        ''' writes the remaining bytes at current offset '''
        len = len(bytes)
        return self.write("{}B".format(len), len)

    # Names
    def unpack_name(self, advance = True):
        ''' Unpacks a single name from a pointer '''
        [ptr] = self.read("I", 4 * advance)
        if not ptr:
            return None
        offset = self.beginOffset + ptr
        nameLens = self.readOffset("I", offset - 4)
        if nameLens[0] > 256:
            print("Name length too long!")
        else:
            name = self.readOffset(str(nameLens[0]) + "s", offset);
            # print("Name: {}".format(name[0]))
            return name[0].decode()

    def storeNameRef(self, name):
        ''' Stores a name reference offset to be filled when packing names
            assumes file to be at name offset to store
            assumes start to be at the parent relation offset
            and advances the file offset
        '''
        map = self.nameRefMap
        if not map.has_key(name):
            map[name] = [(self.beginOffset, file.offset)]
        else:
            map[name].append((self.beginOffset, file.offset))
        self.advance(4)

    def pack_name(self, offset, name):
        ''' packs a single name '''
        len = len(name)
        self.writeOffset("I{}s".format(len), offset -4, len, name)

    def packNames():
        '''packs in the names'''
        map = self.nameRefMap
        names = map.keys()
        names.sort()
        for name in names:
            offset = file.offset + 4
            len = len(name)
            self.write("I{}s".format(len), len + 4, len, name)
            # write name reference pointers
            reflist = map.get(name)
            if not reflist:
                print("Unused name: {}".format(name))
            else:
                for ref in reflist:
                    self.writeOffset("I", ref[1], offset - ref[0])

    def convertByteArr(self):
        if type(self.file) != bytearray:
            self.file = bytearray(self.file)



class FolderEntry:
    ''' A single entry in folder '''
    def __init__(self, parent, idx, name = None, dataPtr = 0):
        self.parent = parent
        self.idx = idx  #  id in relation to folder (first never a data entry)
        self.id = 0xffff    # id, left, right as calculated by binfileary tree
        self.left = 0
        self.right = 0
        self.name = name
        self.dataPtr = dataPtr

    def getName(self):
        return self.name
    def getOffset(self):
        return self.datapointer
    def follow(self, binfile):
        binfile.offset = self.datapointer

    def unpack(self, binfile):
        self.id, u, self.left, self.right = binfile.read("4H", 8)
        self.name = binfile.unpack_name()
        binfile.store()

    def pack(self, binfile):
        self.binfile.write("4H", self.id, 0, self.left, self.right)
        binfile.storeNameRef(self.name)
        if self.dataPtr:
            binfile.write("I", self.dataPtr)
        else:
            binfile.mark()  # marks the ref for storing data

#------------------------------------------------------------------------------
# Most of this courtesy of Wiim http://wiki.tockdom.com/wiki/BRRES_Index_Group_(File_Format)
#    modified slightly to accomodate
    def calc_brres_id(self, objectname):
        ''' Calculates entry id '''
        objlen = len(objectname)
        subjlen = len(self.name)
        if objlen < subjlen:
            self.id =  subjlen - 1 << 3 | self.getHighestBit(self.name[subjlen])
        else:
            while subjlen > 0:
                subjlen -= 1
                ch = objectname[subjlen] ^ self.name[subjlen]
                if ch:
                    self.id = subjlen << 3 | self.getHighestBit(ch)
                    break
        return self.id

    def getHighestBit(val):
        start = 0x80
        i = 7
        while start and not (val & start):
            i -= 1
            start >>= 1
        return i

    def get_brres_id_bit(id):
        idx = id >> 3
        return idx < len(self.name) and self.name[idx] >> (id & 7) & 1

    def calc_brres_entry(entrylist):
        ''' calculates brres entry, given an entry array'''
        head = entrylist[0]
        self.id = self.calc_brres_id("")
        self.left = self.right = self.idx
        prev = head
        current = entrylist[head.left]
        is_right = False
        # loop
        while self.id <= current.id and current.id < prev.id:
            if self.id == current.id:
                # calculate new brres entry
                self.calc_brres_id(current.name)
                if current.get_brres_id_bit(self.id):
                    self.left = self.idx
                    self.right = current.idx
                else:
                    self.left = current.idx
                    self.right = self.idx
            prev = current
            is_right = self.get_brres_id_bit(current.id)
            if is_right:
                current = entrylist[current.right]
            else:
                current = entrylist[current.left]
        if len(current.name) == len(self.name) and current.get_brres_id_bit(self.id):
            self.right = current.idx
        else:
            self.left = current.idx
        if is_right:
            prev.right = self.idx
        else:
            prev.left = self.idx
#    Glad that's over
# --------------------------------------------------------------------------------


class Folder:
    ''' A folder for indexing files with a number of entries. (Index Group)'''
    def __init__(self, binfile, name):
        self.name = name
        self.binfile = binfile
        self.entries = []

    def __len__(self):
        return len(self.entries)

    def __getitem__(self, key):
        return self.entries[key]

    def byteSize(self):
        ''' returns byte size of folder '''
        # headerlen + (numEntries + refEntry) * 16 bytes
        return 8 + (len(self.entries) + 1) * 16

    def addEntry(self, name, dataPtr = 0):
        '''Adds a named entry to folder'''
        l = len(self.entries)
        e = FolderEntry(self, l + 1, name, dataPtr)
        self.entries.append(e)
        return e

    def unpack(self, binfile):
        ''' Unpacks folder '''
        binfile.start()
        self.offset = binfile.offset
        len, numEntries = binfile.read("2I", 8)
        binfile.advance(16) # skip first entry
        for i in range(numEntries):
            sub = FolderEntry(self, i + 1)  # +1 because skips first entry
            sub.unpack(binfile)
            self.entries.append(sub)
        binfile.end()

    def pack(self, binfile):
        ''' packs folder '''
        binfile.start()
        self.offset = binfile.offset
        entries = self.calcEntries()
        len = len(entries)
        binfile.write("2I", len * 16, len - 1) # -1 to ignore reference entry
        for x in entries:
            x.pack(binfile)
        binfile.end()

    def calcEntries(self):
        ''' Calculates the left, right, and id of entries, returns the entries plus the first reference entry '''
        # add on the first reference entry
        head = FolderEntry(self, 0)
        li = [head]
        for x in self.entries:
            li.append(x)
        for x in li:
            x.calc_brres_entry(li)
        return li

    def open(self, name):
        ''' opens the entry with name '''
        try:
            return self.recallEntry(name)
        except:
            return False

    def openI(self, index = 0):
        ''' opens entry at index, returns false on failure '''
        try:
            return self.recallEntryI(index)
        except:
            return False


    def recallEntry(self, name):
        '''Advances to the file offset for unpacking (once only)'''
        for i in range(len(self.entries)):
            if self.entries[i].name == name:
                return self.recallEntryI(i)
        raise ValueError("Entry name {} not in folder {}".format(name, self.name))

    def recallEntryI(self, index = 0):
        ''' Recalls entry at index (once only)'''
        entry = self.entries.pop(index)
        self.binfile.recallOffset(self.offset, index)
        return entry.name

    def createEntryRef(self, name):
        '''creates the reference in folder to the section (data pointer)'''
        for i in range(len(self.entries)):
            if self.entries[i].name == name:
                return self.createEntryRefI(i)
        raise ValueError("Entry name {} not in folder {}".format(name, self.name))

    def createEntryRefI(self, index = 0):
        ''' creates reference in folder to section at entry[index] (once only, pops)'''
        self.entries.pop(index)
        return self.binfile.createRefFrom(self.offset, index + 1)   # index + 1 ignoring the first ref entry

def printCollectionHex(collection, prefix = ""):
    st = ""
    i = 0
    for x in collection:
        st += "{0:02X} ".format(x)
        if i % 16 == 15:
            print("{}".format(st))
            st = ""
        i += 1
    print("{}".format(st))
