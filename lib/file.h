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
#endif
