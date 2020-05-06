#ifndef __TABLE_H
#define __TABLE_H
/***********************************************************
*   Table header file
************************************************************/
#include "str.h"
#include "vector.h"
#include <stdarg.h>

typedef struct _Table {
   String ** header;
   int columns;
   Vector * dataRows;
   int * colOffsets; // the offsets of columns
   FreeFunc freeFunc;
} Table;

// the variable arguments is the size of each column type
Table * table_new(FreeFunc freeFunc, int rows, int cols, ...);

void table_destroy(Table * table);

void table_addHeader(Table * table,...);

int table_rowCount(Table * table) {    return table->dataRows->size;  }
int table_colCount(Table * table) {    return table->columns; }

void table_addRow(Table * table,...);

void * table_getRow(Table * table, int row);

void table_deleteRow(Table * table, int row);

void table_insertRow(Table * table, int row, ...);

void table_swapRows(Table * table, int row1, int row2);

void table_fillRow(Table * table, int row, void * value);
void table_fillColumn(Table * table, int col, void * value);

void * table_getByName(Table * table, int row, String * col);
void * table_get(Table * table, int row, int col);

void table_set(Table * table, int row, int col, void * data);

void table_setByName(Table * table, int row, String * name, void * data);

int table_findName(Table * table, String * name);

#endif
