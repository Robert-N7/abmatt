/******************************************************
* Blight stuff
/******************************************************/
#include "blight.h"
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include "lib/file.h"
#include "lib/stringUtil.h"
#include <string.h>
#include <unistd.h>
#include <ctype.h>
const int BL_FILESIZE = 0x5a8;
BinTemplate * BL_TEMPLATE;

int main(int argc, char ** argv) {
   char * usage = "Usage: %s <filename> [-o] [-d <destination>] [-section {lobj|ambient} -index <i> -key <key> -value <value> [-element <i>]]\n";
   if(argc < 2) {
      fprintf(stderr, usage, argv[0]);
      exit(0);
   }
   bool overwrite = 0;
   bool flagstart = false;
   int sectionIndex = 0, elementIndex = 0;
   String *section = 0, *index = 0, *key = 0, *value = 0;
   char *c, flag, * destination = 0, *source = 0;
   for(int i = 1; i < argc; i++) {
      c = argv[i];
      if(flagstart) {
         if(*c == '-') {
            fprintf(stderr, "Flag %c requires a parameter\n", flag);
            fprintf(stderr, usage, argv[0]);
            exit(0);
         }
         if(flag == 'd')
            destination = c;
         else if(flag == 's') {
            section = str(c);
         } else if(flag == 'i') {
            index = str(c);
            if(tolower(*c) == 'a') {
               sectionIndex = -1;
            } else {
               sectionIndex = atoi(index->str);
            }
         } else if(flag == 'k') {
            key = str(c);
         } else if(flag == 'v') {
            value = str(c);
         } else if(flag == 'e') {
            elementIndex = atoi(c);
         }
         else {
            fprintf(stderr, "Unknown flag %c\n", flag);
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
            flag = tolower(c[1]);
         }
      } else if(source)
         fprintf(stderr, "Unknown parameter %s\n", c);
      else {
         source = c;
      }
   }
   if(flagstart) {
      fprintf(stderr, "Flag %c requires a parameter\n", flag);
      fprintf(stderr, usage, argv[0]);
      exit(0);
   }
   bool err = false;
   if(value || key || section || index) {
      if(!section)
         section = str("lobj");
      if(!key) {
         fprintf(stderr, "Key is required.\n");
         fprintf(stderr, usage, argv[0]);
         exit(0);
      }
      if(!value) {
         fprintf(stderr, "Value is required.\n");
         fprintf(stderr, usage, argv[0]);
         exit(0);
      }
      if(!index) {
         fprintf(stderr, "Index is required.\n");
         fprintf(stderr, usage, argv[0]);
         exit(0);
      } else if(sectionIndex < -1 || sectionIndex > 15) {
         fprintf(stderr, "Index %d is not in valid range, must be 0-15 or (A)ll\n", sectionIndex);
         fprintf(stderr, usage, argv[0]);
         exit(0);
      }
   }
   printf("Finished parsing\n");
   bl_template_init();
   BinFile * bin = bin_new(BL_TEMPLATE, BL_FILESIZE);
   if(!bin_read(bin, source)) {
      printf("Failed to read file\n");
      bin_destroy(bin);
      exit(0);
   }
   // todo changes based on parameters.. and shortcut to exit
   Blight * bl = blight_read(bin);
   GTable * mytable = blight_initialize_table(bl);
   gtable_print(mytable);
   bool quit = false, hasSaved = true;
   if(!destination)
      destination = source;
   String * s, *dest = str(destination);
   while(!quit) {
      s = str_get();
      if(s->str[0] == 'q' || s->str[0] == 'Q') {
         quit = true;
      } else if(strc_in_ignore_case(s, "save", 0) == 0) {
         // todo better command processing
         blight_save(bl, mytable, bin, dest, 0);
      } else {
         gtable_processInput(mytable, s);
      }
      str_free(s);
   }

   // blight_to_string(bl);
   bin_destroy(bin);
   bin_template_destroy(BL_TEMPLATE);
   free(bl);
   str_free(index);
   str_free(key);
   str_free(value);
   str_free(section);
   str_free(dest);
   return 0;
}


bool bl_set(BinFile * bin, String * sectionName, int sectionIndex, String * key, String * value, int elementIndex) {
   // attempt to change the value
   BinHub ** hubs = bin_getSection(*bin->head, sectionName->str);
   if(!hubs) {
      fprintf(stderr, "Failed to find section %s\n", sectionName->str);
      return false;
   }

   BinHub * hub = hubs[sectionIndex];
   BinNode * node = bin_getNode(hub->head, key->str);
   if(!node) {
      fprintf(stderr, "Failed to find Key %s\n", key->str);
      return false;
   }

   if(elementIndex > node->size || elementIndex < 0) {
      fprintf(stderr, "Element %d not in range for key %s, max is %d\n", elementIndex, key->str, node->size);
      return false;
   }
   // try converting value appropriately
   char * endptr;
   if(node->type == Float32) {
      float newval = strtof(value->str, &endptr);
      if(endptr != value->str) {
         fprintf(stderr, "%s not a float: %s requires float value.\n", value->str, key->str);
         return false;
      } else {
         ((float * )node->data)[elementIndex] = newval;
      }
   } else if(node->type == Byte) {
      node->data = value->str;
   } else {
      // int
      long intval = strtol(value->str, &endptr, 10);
      if(endptr == value->str) {
         if(node->type == Int16) {
            ((uint16_t * )node->data)[elementIndex] = (uint16_t) intval;
         } else if(node->type == Int8) {
            ((uint8_t *)node->data)[elementIndex] = (uint8_t) intval;
         } else if(node->type == Int64) {
            ((uint64_t *)node->data)[elementIndex] = (uint64_t) intval;
         } else if(node->type == Int32) {
            ((uint32_t *)node->data)[elementIndex] = (uint32_t) intval;
         }
      } else {
         fprintf(stderr, "%s not an int: Key %s requires an integer value.\n", value->str, key->str);
      }
   }

}

void bl_template_init() {
   BinTemplate * template = bin_template_new("blight");
   bin_template_add(template, Byte, "magic", 4);
   bin_template_add(template, Int32, "filesize", 1);
   bin_template_add(template, Int8, "version", 1);
   bin_template_add(template, Byte, "padding", 3);
   bt_add(template, Int32, "unknown0", 1);
   bt_add(template, Int16, "lobjcount", 1);
   bt_add(template, Int16, "ambientcount", 1);
   bt_add(template, Byte, "unknown1", 4);
   bt_add(template, Byte, "paddingend", 16);
   BinTemplate * lobjt = bin_template_new("lobj");
   bt_add(lobjt, Byte, "magic", 4);
   bt_add(lobjt, Int32, "sectionsize", 1);
   bt_add(lobjt, Int8, "version", 1);
   bt_add(lobjt, Byte, "padding", 3);
   bt_add(lobjt, Int32, "uk", 1);
   bt_add(lobjt, Int16, "uk", 1);
   bt_add(lobjt, Int8, "type", 1);
   bt_add(lobjt, Byte, "uk", 1);
   bt_add(lobjt, Int16, "ambientIndex", 1);
   bt_add(lobjt, Int16, "uk", 1);
   bt_add(lobjt, Float32, "origin", 3);
   bt_add(lobjt, Float32, "destination", 3);
   bt_add(lobjt, Float32, "effect", 1);
   bt_add(lobjt, Int8, "rgba", 4);
   bt_add(lobjt, Int32, "uk", 1);
   bt_add(lobjt, Float32, "uk", 3);
   bt_add(lobjt, Byte, "paddingend", 8);
   lobjt->count = 16;
   bin_template_addsub(template, lobjt);
   BinTemplate * ambt  = bin_template_new("ambient");
   bt_add(ambt, Int8, "rgba", 4);
   bt_add(ambt, Byte, "padding", 4);
   ambt->count = 16;
   bin_template_addsub(template, ambt);
   BL_TEMPLATE = template;
   bin_template_print(template);
}

Blight * blight_read(BinFile * bin) {
      Blight * blight = malloc(sizeof(Blight));
      // parse
      BlightHeader * bh = &blight->header;
      BinHub * hub = *bin->head;
      BinNode * node = hub->head;
      // printf("Node type is %2X and size is %d, name is %s\n", node->type, node->size, node->name);
      bh->magic = node->data;
      // printf("Magic is %.*s\n", 4, bh->magic);
      node = node->next;
      // printf("Node node->type is %2X and size is %d, name is %s\n", node->type, node->size, node->name);
      bh->filesize = node->data;
      node = node->next;
      bh->version = node->data;
      node = node->next;
      node = node->next;
      bh->lobjCount = (node = node->next)->data;
      bh->ambientCount = (node = node->next)->data;
      Lobj * lobj;
      BinHub ** lhub = hub->sections[0];
      for(int i = 0; i < 16; i++) {
         node = lhub[i]->head;
         lobj = &blight->lobjs[i];
         lobj->magic = node->data;
         // printf("%->*X\n", size, file);
         lobj->sectionSize = (node = node->next)->data;
         lobj->version = (node = node->next)->data;
         node = node->next->next->next->next;
         lobj->lightType = node->data;
         lobj->ambientIndex = (node = node->next->next)->data;
         node = node->next->next;
         lobj->origin = node->data;
         lobj->destination = (node = node->next)->data;
         lobj->colorEffect = (node = node->next)->data;
         lobj->rgba = (node = node->next)->data;
      }
      Ambient * ambient;
      lhub = hub->sections[1];
      for(int i = 0; i < 16; i++) {
         node = lhub[i]->head;
         ambient = &blight->ambients[i];
         ambient->rgba = node->data;
         uint8_t * rgba = ambient->rgba;
      }
      return blight;
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
      a = blight->ambients[*l.ambientIndex];
      printf("%2d| %2d |%3d|%2X %2X %2X %2X| %6.0f | %6.0f | %6.0f | %6.0f | %6.0f | %6.0f | %2.2f |%2X %2X %2X %2X\n",
         i, *l.lightType, *l.ambientIndex, a.rgba[0], a.rgba[1], a.rgba[2], a.rgba[3],
         l.origin[0], l.origin[1], l.origin[2],
         l.destination[0], l.destination[1], l.destination[2],
         *l.colorEffect, l.rgba[0], l.rgba[1], l.rgba[2], l.rgba[3]);
   }
   printf("%s\n", table_head);
   printf("%s\n", table_head);
}

GTable * blight_initialize_table(Blight * blight) {
   GTable * table = gtable_new(0, 16, 17, bt_UInt8, bt_UInt16,
       bt_UInt8, bt_UInt8, bt_UInt8, bt_UInt8, // ambient RGBA
       bt_Float32, bt_Float32, bt_Float32,  // origin
       bt_Float32, bt_Float32, bt_Float32,  // dest
       bt_Float32, bt_UInt8, bt_UInt8, bt_UInt8, bt_UInt8); // RGBA

   gtable_addHeader(table, str("Lig"), str("AmI"), str("AmR"), str("AmG"), str("AmB"), str("AmA"),
      str("OriginX"), str("OriginY"), str("OriginZ"),
      str("DestinX"), str("DestinY"), str("DestinZ"),
      str("Effect"), str("LiR"), str("LiG"), str("LiB"), str("LiA"));

   Lobj * lobj;
   uint8_t * amRGBA;
   for(int i = 0; i < 16; i++) {
      lobj = & blight->lobjs[i];
      amRGBA = blight->ambients[i].rgba;
      gtable_addRow(table, lobj->lightType, lobj->ambientIndex, amRGBA, amRGBA + 1, amRGBA + 2, amRGBA + 3,
         lobj->origin, lobj->origin + 1, lobj->origin + 2,
         lobj->destination, lobj->destination + 1, lobj->destination + 2,
         lobj->colorEffect, lobj->rgba, lobj->rgba + 1, lobj->rgba + 2, lobj->rgba + 3);
   }
   return table;
}

void blight_saveTable(Blight * blight, GTable * table) {
   Lobj * lobj;
   Ambient * am;
   for(int i = 0; i < 16; i++) {
      lobj = &blight->lobjs[i];
      *(lobj->ambientIndex) = *((uint16_t * ) gtable_get(table, i, 1));
      am = &blight->ambients[*lobj->ambientIndex];
      gtable_getRow(table, i, lobj->lightType, lobj->ambientIndex, am->rgba, am->rgba + 1, am->rgba + 2, am->rgba + 3,
         lobj->origin, lobj->origin + 1, lobj->origin + 2,
         lobj->destination, lobj->destination + 1, lobj->destination + 2,
         lobj->colorEffect, lobj->rgba, lobj->rgba + 1, lobj->rgba + 2, lobj->rgba + 3);
   }
}

void blight_save(Blight * blight, GTable * table, BinFile * file, String * destination, bool overwrite) {
   blight_saveTable(blight, table);
   if(file_exists(destination->str) && !overwrite) {
      fprintf(stderr, "File '%s' already exists!\n", destination->str);
   } else {
      bin_write(file, destination->str);
   }
}
