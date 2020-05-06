#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include "file.h"
#include <string.h>
#include <stdbool.h>

/*********************************************
*  Library for file functions
*********************************************/

bool file_exists(const char * filename) {
   return access(filename, F_OK) != -1;
}

char * file_read(const char * filename) {
   FILE * fptr = fopen(filename, "r");
   if(!fptr)
     return NULL;
   fseek(fptr, 0, SEEK_END);
   long fsize = ftell(fptr);
   fseek(fptr, 0, SEEK_SET);  /* same as rewind(f); */
   char *result = malloc(fsize + 1);
   fread(result, 1, fsize, fptr); // read the file in
   fclose(fptr);
   result[fsize] = 0;
   return result;
}

int file_write(const char * filename, const char * str) {
   FILE * fptr = fopen(filename, "w");
   if(!fptr)
      return 0;
   int result = fputs(str, fptr);
   fclose(fptr);
   return result;
}

int file_append(const char * filename, const char * str) {
   FILE * fptr = fopen(filename, "a");
   if(!fptr)
      return 0;
   int result = fputs(str, fptr);
   fclose(fptr);
   return result;
}
