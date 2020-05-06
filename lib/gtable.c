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
  int width = sizeof(int) * cols;
  n->colWidths = malloc(width);
  bzero(n->colWidths, width);
  n->colTypes = malloc(width);
  int * colSizes = malloc(width);
  int
  va_list list;
  va_start(list, cols);
  for(int i = 0; i < cols; i++) {
    colSizes[i] = bt_size((n->colTypes[i] = va_arg(list, int)));
  }
  va_end(list)
  n->table = table_anew(freeFunc, rows, cols, colSizes);
  free(colSizes);
  n->isFixedSize = 0;
  return n;
}

void gtable_destroy(GTable * table) {
   table_destroy(table->table);
   free(table->colWidths);
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
   int bitSize;
   for(int i = 0; i < table->columns; i++) {
      // todo

   }
}

void gtable_setColWidth(GTable * table, int col, int width) {
   table->colWidths[col] = width;
}

void gtable_processInput(GTable * table, String * input) {

}

void gtable_print(GTable * table) {
   // print header
   String ** header = table->table->header;
   printf(" id|");
   for(int i = 0; i < table->table->columns; i++) {
      str_printn(header[i]->str, table->colWidths[i]);
      printf("|");
   }
   // print rows
   void * row;
   for(int i = 0; i < table_rowCount(table); i++) {
      printf("%3d|", i);
      row = table_getRow(table, i);
   }
}

void gtable_printRow(GTable * table) {
   // generate format string

   for(int j = 0; j < table_colCount(table); j++) {

   }
}
