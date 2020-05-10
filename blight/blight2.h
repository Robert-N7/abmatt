#ifndef __BLIGHT_H
#define __BLIGHT_H
/******************************************************
* Blight stuff
/******************************************************/
#include <stdint.h>
#include <stdbool.h>
#include "../lib/str.h"

typedef struct _BlightHeader {
   char magic[4];
   uint32_t filesize;
   uint8_t version;
   char padding[3];
   uint32_t unknown0;
   uint16_t lobjCount;
   uint16_t ambientCount;
   char unknown1[4];
   char paddingend[16];
} BlightHeader;

typedef struct _Lobj {
   char magic[4];
   uint32_t sectionSize;
   uint8_t version;
   char padding[3];
   uint32_t unknown0;
   uint16_t unknown1;
   uint8_t lightType;
   char unknown2;
   uint16_t ambientIndex;
   uint16_t unknown3;
   float origin[3];
   float destination[3];
   float colorEffect;
   uint8_t rgba[4];
   uint32_t unknown4;
   float unknown5;
   float unknown6;
   float unknown7;
   char paddingend[8];
} Lobj;

typedef struct _Ambient {
   uint8_t rgba[4];
   char padding[4];
} Ambient;

typedef struct _Blight {
   BlightHeader header;
   Lobj lobjs[16];
   Ambient ambients[16];
} Blight;


Blight * blight_read(char * filename);

void blight_write(Blight * blight, char * filename);

void blight_to_string(Blight * blight);

#endif
