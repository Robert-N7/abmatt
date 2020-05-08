/*********************************************************************
*  String library
**********************************************************************/
#ifndef __STR_H
#define __STR_H

#include <stdbool.h>
#include "vector.h"

// string structure
typedef struct _String {
   int len;
   int capacity;
   char * str;
} String;

#define STR_NOT_FOUND -1
#define STR_END -1

// constructor
String * str(char * s);

// same as above but with size determined
String * str_(char * s, int size);

// destructor
void str_free(String * str);

// for creating a string to be filled
String * str_empty(int capacity);

// copy
String * str_copy(const String * str);

// Join
String * str_join(const String * str1, const String * str2);

// Add
void str_add(String * str1, const String * str2);

// append
void str_append(String * str, const char * cptr, int length);

// slice from [start:end)
String * str_slice(const String * str1, int start, int end);

// Replace
String * str_replace(const String * haystack, const String * needle, const String * replacement, int count);

// is string in - returns -1 if not found
int str_in(const String * haystack, const String * needle, int start);

// is string in - returns -1 if not found
int str_in_ignore_case(const String * haystack, const String * needle, int start);

// is string in - returns -1 if not found
int strc_in_ignore_case(const String * haystack, const char * needle, int start);

// upper
void str_upper(String * string);

// lower
void str_lower(String * string);

// print
void str_print(String * string);

// print up to n characters
void str_printn(String * string, int n);

// err
void str_err(String * string);

// write
int str_write(String * str, int fd);

// read
String * str_read(int fd, int amount);

// trim a string
int str_trim(String * str, const char * chrs);

bool str_eq(const String * s1, const String * s2);

bool str_eq_ignore_case(const String * s1, const String * s2);

Vector * str_split(const String * haystack, const String * needle);

// c string compatibility
bool strc_eq(const String * s1, const char * s2);

bool strc_eq_ignore_case(const String * s1, const char * s2);

String * strc_replace(const String * haystack, const char * needle, const char * replacement, int count);

int strc_in(const String * haystack, const char * needle, int start);

Vector * strc_split(const String * haystack, const char * needle);

#endif
