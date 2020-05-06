#ifndef __SERIALIZE_H
#define __SERIALIZE_H
/**************************************************
* Serializing data to and from files
**************************************************/
#include <stdbool.h>
#include <stdint.h>


#define Int64 0x4000
#define Int32 0x2000
#define Int16 0x1000
#define Int8  0x0800
#define Float32 0x2100
#define Byte  0x0900
#define BIN_SECTION 0xfc00
#define bt_add(t, type, name, count) bin_template_add(t, type, name, count)

typedef int S_TYPE;
typedef struct _binFile BinFile;

typedef struct _binTemplate {
   int size; // current number of members
   int capacity; // current capacity
   int count; // the amount of times to repeat template
   int subCount; // number of subtemplates
   char * name;
   S_TYPE * template;
   char ** typenames;
   struct _binTemplate ** subtemplates; // templates under this one
} BinTemplate;

typedef struct _binNode {
   S_TYPE type;
   int size;
   char * name;
   void * data;
   struct _binNode * next;
} BinNode;

typedef struct _binHub {
   int sectionSize;
   BinNode * head;
   char * sectionName;
   struct _binHub *** sections; // pointer to array of hubs
} BinHub;

typedef struct _binFile {
   int filesize;
   char * filename;
   BinTemplate * template;
   BinHub ** head;
} BinFile;


BinTemplate * bin_template_new(const char * name);

void bin_template_add(BinTemplate * bintemp, S_TYPE type, char * name, int count);

void bin_template_addsub(BinTemplate * bintemp, BinTemplate * subtemp);

BinFile * bin_new(BinTemplate * template, int filesize);

void bin_template_destroy(BinTemplate * bintemp);

void bin_destroy(BinFile * file);
void bin_hubdestroy(BinHub ** hub, BinTemplate * template);

BinHub * bin_getSection(BinHub * hub, char * sectionname);

BinNode * bin_getNode(BinNode * head, char * name);

BinNode * bin_advance(BinNode * node, int amount);

BinHub ** bin_read(BinFile * file, char * filename);

// reads section(s) based on template
BinHub ** bin_read_section(BinTemplate * template, char * data, int * offset);


bool bin_write(BinFile * file, char * filename);

// writes section(s) to buffer
bool bin_write_section(BinTemplate * template, char * data, int * offset, BinHub ** hubs);


void read_bytes(char * input, char * buffer, int * offset, int numBytes);

uint64_t read_int64(void * input, uint64_t * it, int * offset);

uint32_t read_int32(char * input, uint32_t * it, int * offset);

uint16_t read_int16(char * input, uint16_t * it, int * offset);

uint8_t read_int8(char * input, uint8_t * it, int * offset);

float read_float(char * input, float * fl, int * offset);

// binary writing
void write_bytes(char * writeBuffer, char * in, int * offset, int numBytes);

void write_int64(char * writeBuffer, uint64_t it, int * offset);

void write_int32(char * writeBuffer, uint32_t it, int * offset);

void write_float(char * writeBuffer, float fl, int * offset);

void write_int16(char * writeBuffer, uint16_t it, int * offset);

void write_int8(char * writeBuffer, uint8_t it, int * offset);

void bin_template_print(BinTemplate * template);
#endif
