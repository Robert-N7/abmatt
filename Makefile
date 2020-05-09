Blight: blight.o \
	file.o stringUtil.o str.o serialize.o \
	linkedList.o table.o vector.o map.o gtable.o basicTypes.o
	gcc -o Blight.out blight.o \
	file.o stringUtil.o str.o serialize.o \
	linkedList.o table.o vector.o map.o gtable.o basicTypes.o

blight.o: blight.c blight.h
	gcc -c blight.c

# Library files
file.o: lib/file.c lib/file.h
	gcc -c lib/file.c

str.o: lib/str.c lib/str.h
	gcc -c lib/str.c

stringUtil.o: lib/stringUtil.c lib/stringUtil.h
	gcc -c lib/stringUtil.c

serialize.o: lib/serialize.c lib/serialize.h
	gcc -c lib/serialize.c

linkedList.o: lib/linkedList.c lib/linkedList.h
	gcc -c lib/linkedList.c

basicTypes.o:  lib/basicTypes.c lib/basicTypes.h
	gcc -c lib/basicTypes.c

gtable.o:  lib/gtable.c lib/gtable.h lib/table.h
	gcc -c lib/gtable.c

table.o:  lib/table.c lib/table.h
	gcc -c lib/table.c

map.o:  lib/map.c lib/map.h
	gcc -c lib/map.c

vector.o:  lib/vector.c lib/vector.h
	gcc -c lib/vector.c

# Clean
clean:
	rm *.o BLight *.gch *.out
