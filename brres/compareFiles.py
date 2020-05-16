#!/usr/bin/Python
import sys

def compareFiles(fname1, fname2):
    file1 = open(fname1, "rb")
    byteString = file1.read()
    file1.close()
    file2 = open(fname2, "rb")
    byteString2 = file2.read()
    file2.close()
    for i in range(len(byteString)):
        if byteString[i] != byteString2[i]:
            print("Mismatch at offset {}!".format(i))
            print("{}\n\t:{}".format(fname1, byteString[i:i+10]))
            print("{}\n\t:{}".format(fname2, byteString2[i:i+10]))

if __name__ == "__main__":
    args = sys.argv
    if(len(args) < 3):
        print("Not enough parameters.")
        print("tmp.py file1 file2")
        sys.exit(2)
    compareFiles(args[1], args[2])
