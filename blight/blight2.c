/******************************************************
* Blight stuff
/******************************************************/
#include "blight2.h"
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include "../lib/str.h"
#include "../lib/file.h"
#include "../lib/stringUtil.h"
#include "../lib/serialize.h"
#include <string.h>
#include <unistd.h>

int main(int argc, char ** argv) {
   char * usage = "Usage: %s <filename> [-o] [-d <destination>]\n";
   if(argc < 2) {
      fprintf(stderr, usage, argv[0]);
      exit(0);
   }
   bool overwrite = 0;
   bool flagstart = false;
   char * destination = 0;
   char *c, *flag;
   for(int i = 1; i < argc; i++) {
      c = argv[i];
      if(flagstart) {
         if(*c == '-') {
            fprintf(stderr, "Flag %s requires a parameter\n", flag);
            fprintf(stderr, usage, argv[0]);
            exit(0);
         }
         if(*flag == 'd')
            destination = c;
         else {
            fprintf(stderr, "Unknown flag %s\n", flag);
            fprintf(stderr, usage, argv[0]);
            exit(0);
         }
         flagstart = 0;
      }
      else if(*c == '-') {
         if(c[1] == 'o')
            overwrite = true;
         else {
            flagstart = true;
            flag = c + 1;
         }
      }
   }
   if(flagstart) {
      fprintf(stderr, "Flag %s requires a parameter\n", flag);
      fprintf(stderr, usage, argv[0]);
      exit(0);
   }
   printf("Finished parsing\n");
   Blight * bl = blight_read(argv[1]);
   blight_to_string(bl);
   if(!destination)
      destination = argv[1];
   if(file_exists(destination) && !overwrite) {
      fprintf(stderr, "File '%s' already exists!\n", destination);
   } else {
      blight_write(bl, destination);
   }
}


Blight * blight_read(char * filename) {
   FILE * fptr = fopen(filename, "rb");
   if(fptr) {
      int size = sizeof(Blight);
      printf("Size is %X\n", size);
      char * file = malloc(size);
      fread(file, size, 1, fptr);
      fclose(fptr);

      Blight * blight = malloc(size);
      // printf("%X\n", file);
      for(int i = 0; i < size; i++) {
         printf("%02X", file[i]);
         // if(i % 4 == 3)
            printf(" | ");
      }
      // parse
      int offset = 0;
      BlightHeader * bh = &blight->header;
      memcpy(bh->magic, file, 4);
      printf("Magic is %.*s\n", 4, bh->magic);
      offset += 4;
      bh->filesize = read_int32(file, &offset);
      printf("File size is %d\n", bh->filesize);
      memcpy(&bh->version, file + offset, 1);
      printf("Version is %d\n", bh->version);
      offset += 1;
      memcpy(&bh->padding, file + offset, 3);
      offset += 3;
      bh->unknown0 = read_int32(file, &offset);
      bh->lobjCount = read_int16(file, &offset);
      printf("Lobj count is %d\n", bh->lobjCount);
      bh->ambientCount = read_int16(file, &offset);
      memcpy(&bh->unknown1, file + offset, 4);
      offset += 4;
      memcpy(&bh->paddingend, file + offset, 16);
      offset = 40;
      Lobj * lobj;
      for(int i = 0; i < 16; i++) {
         lobj = &blight->lobjs[i];
         memcpy(&lobj->magic, file + offset, 4);
         // printf("%->*X\n", size, file);
         printf("Magic is %.*s\n", 4, lobj->magic);
         offset += 4;
         for(int i = 0; i < 4; i++) {
            printf("%02X\t", file[offset + i]);
         }
         lobj->sectionSize = read_int32(file, &offset);
         memcpy(&lobj->version, file + offset, 1);
         offset += 1;
         read_bytes(&lobj->padding, file, &offset, 3);
         lobj->unknown0 = read_int32(file, &offset);
         printf("Unknown 0 is %d\n", lobj->unknown0);
         lobj->unknown1 = read_int16(file, &offset);
         printf("Unknown 1 is %d\n", lobj->unknown1);
         read_bytes(&lobj->lightType, file, &offset, 1);
         printf("Light type is %d\n", lobj->lightType);
         read_bytes(&lobj->unknown2, file, &offset, 1);
         printf("Unknown 2 is %d\n", lobj->unknown2);
         lobj->ambientIndex = read_int16(file, &offset);
         printf("Ambient index is %d\n", lobj->ambientIndex);
         lobj->unknown3  = read_int16(file, &offset);
         printf("Unknown 3 is %d\n", lobj->unknown3);
         for(int i = 0; i < 12; i++) {
            printf("%02X\t", file[i + offset]);
         }
         for(int i = 0; i < 3; i++) {
            lobj->origin[i] = read_float(file, &offset);
            printf("Read float %.2f\n", lobj->origin[i]);
         }
         printf("Origin is %.2f, %.2f, %.2f\n", lobj->origin[0], lobj->origin[1], lobj->origin[2]);
         for(int i = 0; i < 3; i++)
            lobj->destination[i] = read_float(file, &offset);
         printf("Destination is %.2f, %.2f, %.2f\n", lobj->destination[0], lobj->destination[1], lobj->destination[2]);
         lobj->colorEffect = read_float(file, &offset);
         printf("Color effect is %f\n", lobj->colorEffect);
         read_bytes(&lobj->rgba, file, &offset, 4);
         printf("R:%d G:%d B:%d A:%d\n", lobj->rgba[0], lobj->rgba[1], lobj->rgba[2], lobj->rgba[3]);
         lobj->unknown4 = read_int32(file, &offset);
         printf("Unknown 4 is %d\n", lobj->unknown4);
         lobj->unknown5 = read_float(file, &offset);
         printf("Unknown 5 is %f\n", lobj->unknown5);
         lobj->unknown6 = read_float(file, &offset);
         printf("Unknown 6 is %f\n", lobj->unknown6);
         lobj->unknown7 = read_float(file, &offset);
         printf("Unknown 7 is %f\n", lobj->unknown7);
         read_bytes(&lobj->paddingend, file, &offset, 8);
      }
      Ambient * ambient;
      for(int i = 0; i < 16; i++) {
         ambient = &blight->ambients[i];
         read_bytes(&ambient->rgba, file, &offset, 4);
         read_bytes(&ambient->padding, file, &offset, 4);
      }
      free(file);
      return blight;
   }
   return NULL;
}

void blight_write(Blight * blight, char * filename) {
   FILE * fptr = fopen(filename, "wb");
   if(fptr) {
      char * buffer = malloc(sizeof(Blight));
      bzero(buffer, sizeof(Blight));
      BlightHeader * bh = & blight->header;
      int offset = 0;
      write_bytes(buffer, bh->magic, &offset, 4);
      write_int32(buffer, bh->filesize, &offset);
      printf("File size is %02X\n", buffer[offset - 2]);
      printf("File size is %02X\n", buffer[offset - 1]);
      printf("File version is %d\n", bh->version);
      write_bytes(buffer, &bh->version, &offset, 1);
      printf("Wrote version\n");
      write_bytes(buffer, bh->padding, &offset, 3);
      printf("Wrote padding\n");
      write_int32(buffer, bh->unknown0, &offset);
      write_int16(buffer, bh->lobjCount, &offset);
      write_int16(buffer, bh->ambientCount, &offset);
      printf("Writing unknown 1\n");
      write_bytes(buffer, bh->unknown1, &offset, 4);
      write_bytes(buffer, bh->paddingend, &offset, 16);
      printf("Beginning Lobsj\n");
      Lobj *lobj;
      for(int i = 0; i < 16; i++) {
         lobj = &blight->lobjs[i];
         write_bytes(buffer, lobj->magic, &offset, 4);
         write_int32(buffer, lobj->sectionSize, &offset);
         write_bytes(buffer, &lobj->version, &offset, 1);
         write_bytes(buffer, lobj->padding, &offset, 3);
         printf("Wrote padding\n");
         write_int32(buffer, lobj->unknown0, &offset);
         write_int16(buffer, lobj->unknown1, &offset);
         printf("Writing light type\n");
         write_bytes(buffer, &lobj->lightType, &offset, 1);
         printf("unknown2\n");
         write_bytes(buffer, &lobj->unknown2, &offset, 1);
         printf("ambient\n");
         write_int16(buffer, lobj->ambientIndex, &offset);
         printf("unknown3\n");
         write_int16(buffer, lobj->unknown3, &offset);
         printf("Loop index %d writing float.\n", i);
         write_float(buffer, lobj->origin[0], &offset);
         write_float(buffer, lobj->origin[1], &offset);
         write_float(buffer, lobj->origin[2], &offset);
         write_float(buffer, lobj->destination[0], &offset);
         write_float(buffer, lobj->destination[1], &offset);
         write_float(buffer, lobj->destination[2], &offset);
         write_float(buffer, lobj->colorEffect, &offset);
         write_bytes(buffer, lobj->rgba, &offset, 4);
         write_int32(buffer, lobj->unknown4, &offset);
         write_float(buffer, lobj->unknown5, &offset);
         write_float(buffer, lobj->unknown6, &offset);
         write_float(buffer, lobj->unknown7, &offset);
         write_bytes(buffer, lobj->paddingend, &offset, 8);
      }
      Ambient * am;
      for(int i = 0; i < 16; i++) {
         am = &blight->ambients[i];
         write_bytes(buffer, am->rgba, &offset, 4);
         write_bytes(buffer, am->padding, &offset, 4);
      }
      fwrite(buffer, sizeof(Blight), 1, fptr);
      fclose(fptr);
      free(buffer);
   }
}


void blight_to_string(Blight * blight) {
   char * table_head = "------------------------------------------------------------------------------------------------";
   printf("%s\n", table_head);
   printf("id|Type|Amb|Ambient RGB|Origin X|Origin Y|Origin Z|Destin X|Destin Y|Destin Z|Effect|RGBA\n");
   printf("%s\n", table_head);
   Lobj l;
   Ambient a;
   for(int i = 0; i < 16; i++) {
      l = blight->lobjs[i];
      a = blight->ambients[l.ambientIndex];
      printf("%2d| %2d |%3d|%2X %2X %2X %2X| %6.0f | %6.0f | %6.0f | %6.0f | %6.0f | %6.0f | %2.2f |%2X %2X %2X %2X\n",
         i, l.lightType, l.ambientIndex, a.rgba[0], a.rgba[1], a.rgba[2], a.rgba[3],
         l.origin[0], l.origin[1], l.origin[2],
         l.destination[0], l.destination[1], l.destination[2],
         l.colorEffect, l.rgba[0], l.rgba[1], l.rgba[2], l.rgba[3]);
   }
   printf("%s\n", table_head);
   printf("%s\n", table_head);
}
