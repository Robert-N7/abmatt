Blight: blight.o file.o stringUtil.o str.o serialize.o
	gcc -o Blight blight.o file.o stringUtil.o str.o serialize.o

blight.o: blight.c blight.h
	gcc -c blight.c

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

clean:
	rm *.o BLight
