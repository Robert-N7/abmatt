#!/usr/bin/Python
xlufile = open("course_model.brres", "rb")
byteString = xlufile.read()
xlufile.close()
opaquefile = open("course_modelOpaque.brres", "rb")
byteString2 = opaquefile.read()
opaquefile.close()
for i in range(len(byteString)):
    if byteString[i] != byteString2[i]:
        print("Mismatch at offset {}!".format(i))
        print("\t:{}".format(byteString[i:i+10]))
        print("\t:{}".format(byteString2[i:i+10]))
