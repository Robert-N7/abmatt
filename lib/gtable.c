/*******************************************
*   implementation for graphical tables
*******************************************/
#include "gtable.h"
#include <stdlib.h>
#include "table.h"
#include "basicTypes.h"

// ... = basic types
GTable * gtable_new(FreeFunc freeFunc, int rows, int cols, ...) {
  GTable * n = malloc(sizeof(GTable));
  n->formatCol = malloc(sizeof(String *) * cols);
  int width = sizeof(int) * cols;
  n->colTypes = malloc(width);
  int * colSizes = malloc(width);
  va_list list;
  va_start(list, cols);
  for(int i = 0; i < cols; i++) {
    colSizes[i] = bt_size((n->colTypes[i] = va_arg(list, int)));
  }
  va_end(list)
  n->table = table_anew(freeFunc, rows, cols, colSizes);
  free(colSizes);
  n->isFixedSize = 0;
  gtable_autoSizeColumns(n);
  return n;
}

void gtable_destroy(GTable * table) {
   table_destroy(table->table);
   for(int i = 0; i < table->columns; i++)
      str_free(table->formatCol[i]);
   free(table->formatCol);
   free(table->colTypes);
   free(table);
}

// ... = default values for row
void gtable_setDefaults(GTable * table, ...) {
   va_list list;
   va_start(list, table);
   table_vsetDefaults(table, list);
   va_end(list);
}

// ... = list of strings
void gtable_addHeader(Gtable * table, ...) {
   va_list list;
   va_start(list, table);
   table_vaddHeader(table->table, list);
   va_end(list);
}

void gtable_autoSizeColumns(GTable * table) {
   bt_Type type;
   for(int i = 0, size; i < table->columns; i++) {
       type = table->colTypes[i];
        if(bt_isInt(type)) {
            if(bt_size(type) > 16)
              table->formatCol[i] = str("5");
            else if(bt_size(type) == 16)
              table->formatCol[i] = str("3");
            else
              table->formatCol[i] = str("2");
        } else if(bt_isFloat(type)) {
          table->formatCol[i] = str("6.1");
        }
   }
}

void gtable_setColFormat(GTable * table, int col, String * format) {
   table->formatCol[col] = format;
}

void gtable_processInput(GTable * table, String * input) {
// <header><index> = <val>
// Fill {<header>|<row>} with <val> [incrementing [by <x>]]
// Row {<n>|<range>} = Row <n>
// Add [<n>] Row(s) [matching row <m>]
// Delete Row(s) [<n>|<range>]
// Insert [<n>] Row(s) at <i>
// Swap Rows <n> and <m>
// Quit
// Save
}

void gtable_print(GTable * table) {
   // print header
   String ** header = table->table->header;
   printf(" id|");
   for(int i = 0, width; i < table->table->columns; i++) {
      if(!(width = atoi(table->formatCol[i])))
        width = 3;
      str_printn(header[i]->str, width);
      printf("|");
   }
   // print rows
   void * row;
   bt_Type type;
   String * tmp;
   int * colOffsets = table->table->colOffsets;
   for(int i = 0; i < table_rowCount(table); i++) {
      printf("%3d|", i);
      row = table_getRow(table, i);
      for(j = 0; j < table->columns; j++) {
        type = table->colTypes[j];
        tmp = bt_toString(type, row + colOffsets[j], 0);
        printf("%s|", tmp->str);
        str_free(tmp);
      }
   }
}
