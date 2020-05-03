Blight: blight.o file.o stringUtil.o str.o
	gcc -o Blight blight.o file.o stringUtil.o str.o

blight.o: blight.c
	gcc -c blight.c

file.o: lib/file.c
	gcc -c lib/file.c

str.o: lib/str.c
	gcc -c lib/str.c

stringUtil.o: lib/stringUtil.c
	gcc -c lib/stringUtil.c

clean:
	rm *.o BLight
