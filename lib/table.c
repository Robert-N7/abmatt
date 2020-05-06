/***********************************************************
*   Table implementation file
************************************************************/
#include "table.h"
#include <stdlib.h>

Table * table_new(FreeFunc freeFunc, int rows, int cols, ...) {
   va_list list;
   va_start(list, cols);
   Table * ret = table_vnew(freeFunc, rows, cols, list);
   va_end(list);
   return ret;
}

Table * table_vnew(FreeFunc freeFunc, int rows, int cols, va_list args) {
  Table * new = malloc(sizeof(Table));
  int * colOffsets = malloc((cols + 1) * sizeof(int));
  colOffsets[0] = 0;
  for(int i = 0, offset = 0; i < cols; i++) {
     offset += va_arg(args, int);
     colOffsets[i + 1] = offset;
  }
  new->colOffsets = colOffsets;
  new->dataRows = vector_new(rows, sizeof(void *), NULL);
  new->defaults = malloc(colOffsets[cols]);
  bzero(new->defaults, colOffsets[cols]);
  new->header = 0;
  new->columns = columns;
  new->header = header;
  new->freeFunc = freeFunc;
  return new;
}

Table * table_anew(FreeFunc freeFunc, int rows, int cols, int * args) {
  Table * new = malloc(sizeof(Table));
  int * colOffsets = malloc((cols + 1) * sizeof(int));
  colOffsets[0] = 0;
  for(int i = 0, offset = 0; i < cols; i++) {
     offset += args[i];
     colOffsets[i + 1] = offset;
  }
  new->colOffsets = colOffsets;
  new->dataRows = vector_new(rows, sizeof(void *), NULL);
  new->defaults = malloc(colOffsets[cols]);
  bzero(new->defaults, colOffsets[cols]);
  new->header = 0;
  new->columns = columns;
  new->header = header;
  new->freeFunc = freeFunc;
  return new;
}

void table_destroy(Table * table) {
   // first take care of the rows of data;
   for(int i = 0; i < table->dataRows->size; i++) {
      void * row = vector_get(table->dataRows, i);
      if(table->freeFunc)
         for(int j = 0; j < table->columns; j++) {
            table->freeFunc(row + table->colOffsets[j]);
         }
      free(row);
   }
   vector_destroy(table->dataRows);
   if(table->freeFunc)
     for(int j = 0; j < table->columns; j++) {
        table->freeFunc(defaults + table->colOffsets[j]);
     }
   free(table->defaults);
   free(table->header);
   free(table->colOffsets);
   free(table);
}

void table_addHeader(Table * table,...) {
   va_list valist;
   va_start(valist, table->columns);
   table_vaddHeader( table, valist);
   va_end(valist);
}

void table_vaddHeader(Table * table, va_list args) {
  if(!table->header)
    table->header = malloc(columns * sizeof(String *));
  String * s;
  for(int i = 0; i < table->columns; i++) {
     s = va_arg(args, String *);
     table->header[i] = s;
  }
}

void table_setDefaults(Table * table,...) {
  va_list list;
  va_start(list, table->columns);
  table_vsetDefaults(table, list);
  va_end(list);
}

void table_vsetDefaults(Table * table, va_list args) {
  void * ptr, *defaults = table->defaults;
  int * offsets = table->colOffsets;
  for(int i = 0; i < table->columns; i++) {
    ptr = va_arg(args, void *);
    memcpy(defaults + offsets[i], ptr, offsets[i + 1] - offsets[i]);
  }
}


void table_addRow(Table * table,...) {
   va_list valist;
   va_start(valist, table->columns);
   table_vaddRow(table, valist);
   va_end(valist);
}

void table_vaddRow(Table * table, va_list args) {
  int * offsets = table->colOffsets;
  void * rowptr = malloc(offsets[table->columns]);
  void * s;
  vector_push(table->dataRows, rowptr);
  for(int i = 0; i < table->columns; i++) {
     s = va_arg(args, void *);
     memcpy(rowptr + offsets[i], s, offsets[i + 1] - offsets[i]);
  }
}

void * table_getRow(Table * table, int row) {
   return vector_get(table->dataRows, row);
}

void table_deleteRow(Table * table, int row) {
   // take care of freeing data?
   void * ptr = vector_get(table->dataRows, row);
   if(table->freeFunc) {
      for(int i = 0; i < table->columns; i++)
         table->freeFunc(ptr + table->colOffsets[i]);
   }
   free(ptr); // free row pointer
   vector_delete(table->dataRows, row);
}

void table_swapRows(Table * table, int row1, int row2) {
   vector_swap(table->dataRows, row1, row2);
}

void table_fillRow(Table * table, int row, void * value) {
   void * rowdata = vector_get(table->dataRows, row);
   void * current;
   int * offsets = table->colOffsets;
   for(int i = 0; i < table->columns; i++) {
      current = rowdata + offsets[i];
      if(table->freeFunc)
         table->freeFunc(current);
      memcpy(current, value, offsets[i + 1] - offsets[i]);
   }
}

void table_fillColumn(Table * table, int col, void * value) {
   int rowCount = table_rowCount(table);
   for(int i = 0; i < rowCount; i++) {
      table_set(table, i, col, value);
   }
}

void * table_getByName(Table * table, int row, String * name) {
   int index = table_findName(table, name);
   return vector_get(table->dataRows, row) + table->colOffsets[index];
}

void * table_get(Table * table, int row, int col) {
   return vector_get(table->dataRows, row) + table->colOffsets[col];
}

void table_set(Table * table, int row, int col, void * data) {
   void * current = vector_get(table->dataRows, row) + table->colOffsets[col];
   if(table->freeFunc)
      table->freeFunc(current);
   memcpy(current, data, table->colOffsets[col + 1] - table->colOffsets[col]);
}

void table_setByName(Table * table, int row, String * name, void * data) {
   int col = table_findName(table, name);
   table_set(table, row, col, data)
}

int table_findName(Table * table, String * name) {
   String ** header = table->header;
   for(int i = 0; i < header; i++) {
      if(header[i] == name) {
         return i;
      }
   }
   return 0;
}
