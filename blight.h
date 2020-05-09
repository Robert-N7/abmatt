#ifndef __BLIGHT_H
#define __BLIGHT_H
/******************************************************
* Blight stuff
/******************************************************/
#include <stdint.h>
#include <stdbool.h>
#include "lib/str.h"
#include "lib/serialize.h"
#include "lib/gtable.h"

typedef struct _BlightHeader {
   char * magic;
   uint32_t * filesize;
   uint8_t * version;
   uint16_t * lobjCount;
   uint16_t * ambientCount;
} BlightHeader;

typedef struct _Lobj {
   char * magic;
   uint32_t * sectionSize;
   uint8_t * version;
   uint8_t * lightType;
   uint16_t * ambientIndex;
   float * origin;
   float * destination;
   float * colorEffect;
   uint8_t * rgba;
} Lobj;

typedef struct _Ambient {
   uint8_t * rgba;
} Ambient;

typedef struct _Blight {
   BlightHeader header;
   Lobj lobjs[16];
   Ambient ambients[16];
} Blight;

void bl_template_init();
Blight * blight_read(BinFile * bin);

bool bl_set(BinFile * bin, String * sectionName, int sectionIndex, String * key, String * value, int elementIndex);

void blight_to_string(Blight * blight);

GTable * blight_initialize_table(Blight * blight);
#endif
