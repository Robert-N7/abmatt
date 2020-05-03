#ifndef __FILE_H
#define __FILE_H
#include <stdint.h>
#include <stdbool.h>
/*********************************************
*  Library for file functions
*********************************************/
bool file_exists(const char * filename);

char * file_read(const char * filename);

int file_write(const char * filename, const char * str);

int file_append(const char * filename, const char * str);

void read_bytes(void * buffer, char * input, int * offset, int numBytes);

uint64_t read_int64(void * input, int * offset);

uint32_t read_int32(char * input, int * offset);

uint16_t read_int16(char * input, int * offset);

uint8_t read_int8(char * input, int * offset);

float read_float(char * input, int * offset);

// binary writing
void write_bytes(char * writeBuffer, char * in, int * offset, int numBytes);

void write_int64(char * writeBuffer, uint64_t it, int * offset);

void write_int32(char * writeBuffer, uint32_t it, int * offset);

void write_float(char * writeBuffer, float fl, int * offset);

void write_int16(char * writeBuffer, uint16_t it, int * offset);

void write_int8(char * writeBuffer, uint8_t it, int * offset);

#endif
