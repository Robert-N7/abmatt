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
  return n;
}

vodi gtable_destroy(GTable * table);

// ... = default values for row
void gtable_setDefaults(GTable * table, ...);

// ... = list of strings
void gtable_addHeader(Gtable * table, ...);

void gtable_setColWidth(GTable * table, int col, int width);

void gtable_processInput(GTable * table, String * input);

void gtable_print(GTable * table);
