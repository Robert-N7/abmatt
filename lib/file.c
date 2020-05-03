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

// Binary reading - big-endian
void read_bytes(void * buffer, char * input, int * offset, int numBytes) {
   memcpy(buffer, input + *offset, numBytes);
   *offset += numBytes;
}

uint64_t read_int64(void * input, int * offset) {
   return read_int32(input + 4, offset) | ((uint64_t) read_int32(input, offset) << 32);
}

uint32_t read_int32(char * input, int * offset) {
   input += *offset;
   uint32_t ret = (uint32_t)(input[0] & 0xff) << 24 | (int)(input[1] & 0xff) << 16 | (int) (input[2] & 0xff) << 8 | (input[3] & 0xff);
   *offset += 4;
   printf("Returning %2X\n", ret);
   return ret;
}

uint16_t read_int16(char * input, int * offset) {
   uint16_t it = (input[*offset + 1] & 0xff) | (uint16_t) (input[*offset] & 0xff) << 8;
   *offset += 2;
   return it;
}

uint8_t read_int8(char * input, int * offset) {
   return input[*offset++] & 0xff;
}

float read_float(char * input, int * offset) {
   int res = read_int32(input, offset);
   return *((float *) &res);
}

// binary writing
void write_bytes(char * writeBuffer, char * in, int * offset, int numBytes) {
   memcpy(writeBuffer + *offset, in, numBytes);
   *offset += numBytes;
}

void write_int64(char * writeBuffer, uint64_t it, int * offset) {
   writeBuffer += *offset;
   for(int i = 0; i < 8; i++) {
      writeBuffer[i] = (it >> (7 - i) * 8) & 0xff;
   }
   *offset += 8;
}

void write_int32(char * writeBuffer, uint32_t it, int * offset) {
   writeBuffer += *offset;
   printf("Writing int %d, at offset %d\n", it, *offset);
   // separate the bytes
   writeBuffer[0] = (it >> 24) & 0xff;
   writeBuffer[1] = (it >> 16) & 0xff;
   writeBuffer[2] = (it >> 8) & 0xff;
   writeBuffer[3] = it & 0xff;
   *offset += 4;
}

void write_float(char * writeBuffer, float fl, int * offset) {
   // force to int
   int * fptr = &fl;
   write_int32(writeBuffer, *fptr, offset);
}

void write_int16(char * writeBuffer, uint16_t it, int * offset) {
   writeBuffer += *offset;
   writeBuffer[0] = (it >> 8) & 0xff;
   writeBuffer[1] = it & 0xff;
   *offset += 2;
}

void write_int8(char * writeBuffer, uint8_t it, int * offset) {
   writeBuffer[*offset++] = it & 0xff;
}
