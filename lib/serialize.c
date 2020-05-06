/**************************************************
* Serializing data to and from files
**************************************************/
#include "serialize.h"
#include <string.h>
#include <stdlib.h>
#include <stddef.h>
#include <stdio.h>

BinTemplate * bin_template_new(const char * name) {
   BinTemplate * ret = malloc(sizeof(BinTemplate));
   int len = strlen(name);
   ret->name = malloc(len + 1);
   ret->name[len] = 0;
   memcpy(ret->name, name, len);
   ret->size = 0;
   ret->capacity = 16;
   ret->count = 1;
   ret->subCount = 0;
   ret->subtemplates = 0;
   ret->template = malloc(sizeof(S_TYPE) * ret->capacity);
   ret->typenames = malloc(sizeof(char * ) * ret->capacity);
   return ret;
}

void bin_template_add(BinTemplate * bintemp, S_TYPE type, char * name, int count) {
   if(count < 1) {
      printf("Unable to add to binary template with count %d\n", count);
      return;
   }
   if(bintemp->size >= bintemp->capacity) {
      bintemp->capacity *= 2;
      S_TYPE * ptr = malloc(sizeof(S_TYPE) * bintemp->capacity);
      memcpy(ptr, bintemp->template, bintemp->size * sizeof(S_TYPE));
      free(bintemp->template);
      bintemp->template = ptr;
      char ** newptr = malloc(sizeof(char *) * bintemp->capacity);
      memcpy(newptr, bintemp->typenames, bintemp->size * sizeof(char *));
      free(bintemp->typenames);
      bintemp->typenames = newptr;
   }
   int len = strlen(name), size = bintemp->size;
   bintemp->template[size] = type | count;
   char * tmp = malloc(sizeof(char) * len + 1);
   tmp[len] = 0;
   memcpy(tmp, name, len);
   bintemp->typenames[size] = tmp;
   bintemp->size += 1;
}

// add sub-template
void bin_template_addsub(BinTemplate * bintemp, BinTemplate * subtemp) {
   int newsize = (bintemp->subCount + 1) * sizeof(BinTemplate *);
   printf("Attempting realoc\n");
   BinTemplate **ptr = realloc(bintemp->subtemplates, newsize);
   if(!ptr) {
      ptr = malloc(newsize);
      if(bintemp->subtemplates) {
         memcpy(ptr, bintemp->subtemplates, bintemp->size);
         free(bintemp->subtemplates);
      }
   }
   bintemp->subtemplates = ptr;
   printf("Finished allocation\n");
   bintemp->subtemplates[bintemp->subCount] = subtemp;
   bintemp->subCount += 1;
   bin_template_add(bintemp, BIN_SECTION, subtemp->name, subtemp->count);
   printf("Finished adding subtemp\n");
}

void bin_template_destroy(BinTemplate * bintemp) {
   for(int i = 0; i < bintemp->size; i++)
      free(bintemp->typenames[i]);
   free(bintemp->typenames);
   free(bintemp->template);
   free(bintemp->name);
   for(int i = 0; i < bintemp->subCount; i++) {
      bin_template_destroy(bintemp->subtemplates[i]);
   }
   free(bintemp->subtemplates);
   free(bintemp);
}

BinFile * bin_new(BinTemplate * template, int filesize) {
   BinFile * file = malloc(sizeof(BinFile));
   file->template = template;
   file->filesize = filesize;
   file->head = NULL;
   file->filename = NULL;
   return file;
}

void bin_destroy(BinFile * file) {
   free(file->filename);
   bin_hubdestroy(file->head, file->template);
   free(file);
}

void bin_hubdestroy(BinHub ** hub, BinTemplate * template) {
   BinNode *tmp;
   BinHub *bh = *hub;
   while(tmp = bh->head) {
      bh->head = tmp->next;
      free(tmp->name);
      free(tmp->data);
      free(tmp);
   }
   for(int i = 0; i < template->count; i++) {
      bh = hub[i];
      // printf("Destroying hub %s with %d sections index %d\n", bh->sectionName, bh->sectionSize, i);
      for(int i = 0; i < bh->sectionSize; i++) {
         bin_hubdestroy(bh->sections[i], template->subtemplates[i]);
      }
      free(bh->sections);
      free(bh->sectionName);
      free(bh);
   }
   free(hub);
}

BinHub * bin_getSection(BinHub * hub, char * sectionname) {
   if(strcmp(sectionname, hub->sectionName) == 0)
      return hub;
   for(int i = 0; i < hub->sectionSize; i++) {
      if(hub = bin_getSection(*(hub->sections[i]), sectionname))
         return hub;
   }
   return NULL;
}

BinNode * bin_getNode(BinNode * head, char * name) {
   for(BinNode * node = head; node; node = node->next) {
      if(strcmp(node->name, name) == 0)
         return node;
   }
   return 0;
}

BinNode * bin_advance(BinNode * node, int amount) {
   for(int i = 0; i < amount; i++)
      node = node->next;
   return node;
}

BinHub ** bin_read(BinFile * file, char * filename) {
   if(filename) {
      int len = strlen(filename);
      if(file->filename)
         free(file->filename);
      file->filename = malloc(len + 1);
      strcpy(file->filename, filename);
   }
   if(!file->filename)
      return NULL;
   FILE * fptr = fopen(file->filename, "rb");
   if(fptr) {
      void * data = malloc(file->filesize);
      // read file
      int result = fread(data, 1, file->filesize, fptr);
      fclose(fptr);
      if(result != file->filesize) {
         printf("Failed to read in the sufficient number of bytes\n");
         free(data);
         return NULL;
      }
      int offset = 0;
      file->head = bin_read_section(file->template, data, &offset);
      free(data);
      return file->head;
   }
   return 0;
}

// reads section(s) based on template
BinHub ** bin_read_section(BinTemplate * template, char * data, int * offset) {
   // array of hubs
   BinHub ** hubs = malloc(sizeof(BinHub *) * template->count);
   BinHub * hub;
   int len = strlen(template->name);
   // set up section(s)
   for(int i = 0; i < template->count; i++) {
      hub = malloc(sizeof(BinHub));
      if(hub->sectionSize = template->subCount)
         hub->sections = malloc(sizeof(BinHub **) * template->subCount);
      hub->sectionName = malloc(len + 1);
      hub->sectionName[len] = 0;
      memcpy(hub->sectionName, template->name, len);
      hub->head = 0;
      hubs[i] = hub;
   }
   S_TYPE type;
   BinNode *node, *prev = 0;
   int typecount, typesize, sectionNum = 0;
   // each section
   // printf("Section %s, %d sections\n", template->name, template->count);
   for(int k = 0, j, i; k < template->count; k++) {
      hub = hubs[k];
      // printf("================================================================\n");
      // printf("Section %s\t%d\n", template->name, k);
      // printf("================================================================\n");
      // each data member
      for(i = 0; i < template->size; i++) {
         type = template->template[i];
         typecount = type & 0xff;
         typesize = (type >> 8) & 0xfc;
         type = type & 0xff00;
         if(type == BIN_SECTION) { // recursive
            if(sectionNum >= hub->sectionSize) {
               printf("Too many sections in template, %d maximum... reading failed\n", sectionNum);
               return NULL;
            }
           hub->sections[sectionNum] = bin_read_section(template->subtemplates[sectionNum], data, offset);
           ++sectionNum;
        } else {  // regular node
            node = malloc(sizeof(BinNode));
            node->data = malloc(typesize * typecount);
            node->size = typecount;
            node->type = type;
            node->next = 0;
            // printf("typename %d is %s\n", i, template->typenames[i]);
            len = strlen(template->typenames[i]);
            node->name = malloc(len + 1);
            node->name[len] = 0;
            memcpy(node->name, template->typenames[i], len);
            // printf("Get '%s' type %2X count %d size %d offset %d\n",\
             node->name, node->type, node->size, typesize, *offset);
            if(prev) {
               prev->next = node;
            }
            if(i == 0)
               hub->head = node;
            if(type == Float32) {
               for(j = 0; j < typecount; j++) {
                  read_float(data, ((float *) node->data) + j, offset);
               }
            } else if(type == Int32) {
               for( j = 0; j < typecount; j++) {
                  read_int32(data, ((uint32_t *) node->data) + j, offset);
               }
            } else if (type == Int16) {
               for( j = 0; j < typecount; j++) {
                  read_int16(data, ((uint16_t *) node->data) + j, offset);
               }
            } else if (type == Int8) {
               for( j = 0; j < typecount; j++) {
                  read_int8(data, ((uint8_t * ) node->data) + j, offset);
               }
            } else if(type == Int64) {
               for( j = 0; j < typecount; j++)
                  read_int64(data, ((uint64_t * ) node->data) + j, offset);
            } else { // read bytes
               read_bytes(data, node->data, offset, typecount);
            }
            // printf("%.*s  ", typesize, node->data);
            prev = node;
         }
      }
   }
   return hubs;
}

bool bin_write(BinFile * file, char * filename) {
   if(filename) {
      free(file->filename);
      int len = strlen(filename);
      file->filename = malloc(len + 1);
      memcpy(file->filename, filename, len);
      file->filename[len] = 0;
   }
   if(!file->filename)
      return 0;
   FILE * fptr = fopen(file->filename, "wb");
   if(!fptr)
      return 0;
   char * data = malloc(file->filesize + 1);
   data[file->filesize] = 0;
   int offset = 0;
   bool result = bin_write_section(file->template, data, &offset, file->head);
   if(!result) {
      printf("Failed to write data\n");
   } else
      fwrite(data, sizeof(char), file->filesize, fptr);
   free(data);
   fclose(fptr);
   return result;
}

// writes section(s) to buffer
bool bin_write_section(BinTemplate * template, char * data, int * offset, BinHub ** hubs) {
   S_TYPE type;
   BinNode *node, *prev = 0;
   BinHub * hub;
   bool result = true;
   int typecount, typesize, sectionNum = 0;
   // printf("Writing Section %s\tmembers %d\tSubsections %d\tCount %d\n", template->name, template->size, template->subCount, template->count);
   // printf("=================================================================================================\n");
   // printf("%s\n", data);
   // printf("=================================================================================================\n");
   // each section
   for(int k = 0, i, j; k < template->count; k++) {
      hub = hubs[k];
      // each data member
      for(i = 0; i < template->size; i++) {
         type = template->template[i] & 0xff00;
         if(type == BIN_SECTION) { // recursive
           if(!bin_write_section(template->subtemplates[sectionNum], data, offset, hub->sections[sectionNum]))
               result = false;
            sectionNum++;
        } else {  // regular node
            if(prev) {
               node = prev->next;
            } else
               node = hub->head;
            if(!node) {
               printf("ERROR: reached end of list\n");
               return false;
            }
            // printf("Writing %s type %2X array size %d offset %d\n", \
            node->name, type, node->size, *offset);
            if(type == Int32) {
               for(j = 0; j < node->size; j++)
                  write_int32(data, ((uint32_t *)node->data)[j], offset);
            } else if(type == Int16) {
               for(j = 0; j < node->size; j++)
                  write_int16(data, ((uint16_t *) node->data)[j], offset);
            } else if(type == Int8) {
               for(j = 0; j < node->size; j++)
                  write_int8(data, ((uint8_t *) node->data)[j], offset);
            } else if(type == Int64) {
               for(j = 0; j < node->size; j++)
                  write_int64(data, ((uint64_t *) node->data)[j], offset);
            } else if(type == Float32) {
               for(j = 0; j < node->size; j++)
                  write_float(data, ((float *)(node->data))[j], offset);
            } else { // default is byte
               write_bytes(data, node->data, offset, node->size);
            }
            prev = node;
         }
      }
   }
}

// Binary reading - big-endian
void read_bytes(char * input, char * buffer, int * offset, int numBytes) {
   memcpy(buffer, input + *offset, numBytes);
   *offset += numBytes;
}

uint64_t read_int64(void * input, uint64_t * it, int * offset) {
   int tmp;
   return *it = read_int32(input + 4, &tmp, offset) | ((uint64_t) read_int32(input, &tmp, offset) << 32);
}

uint32_t read_int32(char * input, uint32_t * it, int * offset) {
   input += *offset;
   *it = (uint32_t)(input[0] & 0xff) << 24 | (int)(input[1] & 0xff) << 16 | (int) (input[2] & 0xff) << 8 | (input[3] & 0xff);
   *offset += 4;
   return *it;
}

uint16_t read_int16(char * input, uint16_t * it, int * offset) {
   *it = (input[*offset + 1] & 0xff) | (uint16_t) (input[*offset] & 0xff) << 8;
   *offset += 2;
   return *it;
}

uint8_t read_int8(char * input, uint8_t * it, int * offset) {
   *it = input[*offset] & 0xff;
   *offset += 1;
   return *it;
}

float read_float(char * input, float * fl, int * offset) {
   int res = read_int32(input, &res, offset);
   return *fl = *((float *) &res);
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
   writeBuffer[*offset] = it & 0xff;
   *offset += 1;
}

void bin_template_print(BinTemplate * template) {
   S_TYPE * types = template->template;
   S_TYPE tmp;
   int count;
   printf("\n=======================================================================\n");
   printf("Template %s\tsize: %d\tsubsections: %d\n", template->name, template->size, template->subCount);
   for(int i = 0; i < template->size; i++) {
      tmp = types[i] & BIN_SECTION;
      count = types[i] & 0xff;
      if(tmp == Float32)
         printf("%s = Float: %d\t", template->typenames[i], count);
      else if(tmp == Int32)
         printf("%s = int32: %d\t", template->typenames[i], count);
      else if(tmp == Int16)
         printf("%s = int16: %d\t", template->typenames[i], count);
      else if(tmp == Int8)
         printf("%s = int8: %d\t", template->typenames[i], count);
      else if(tmp == Int64)
         printf("%s = int64: %d\t", template->typenames[i], count);
      else if(tmp == Byte)
         printf("%s = byte: %d\t", template->typenames[i], count);
      else if(tmp == BIN_SECTION)
         printf("%s = section: %d\t", template->typenames[i], count);
      else
         printf("Unknown type %2X\t", tmp);
   }
   for(int i = 0; i < template->subCount; i++) {
      bin_template_print(template->subtemplates[i]);
   }
   printf("\n=======================================================================\n");
}
