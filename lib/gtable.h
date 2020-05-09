#ifndef __GTABLE_H
#define __GTABLE_H
/***********************************************
*  Header for Graphical tables
*  Command line interface for modifying tables
************************************************/

#include "table.h"
#include "basicTypes.h"
#include "vector.h"
#include <stdarg.h>
#include <stdbool.h>

typedef struct {
   Table * table;
   String ** formatCol;
   int * colTypes;
   bool isFixedSize; // fixed row size?
} GTable;

// ... = basic types
GTable * gtable_new(FreeFunc freeFunc, int rows, int cols, ...);

void gtable_destroy(GTable * table);

// ... = default values for row
void gtable_setDefaults(GTable * table, ...);

// ... = list of strings
void gtable_addHeader(Gtable * table, ...);
// ... = row data
void gtable_addRow(Gtable * table, ...);

void gtable_setColWidth(GTable * table, int col, int width);

void gtable_processInput(GTable * table, String * input);
// Set <column> [<row range>] to <val> [incrementing [by <x>]] [advancing by <y>]
void gtable_set(GTable * table, Vector * input);
// Swap Rows <row range> and <row range>
void gtable_swapRows(GTable * table, Vector * v);
// Replace row(s) <row range> with row(s) <row range> [columns <col range>]
void gtable_replaceRows(GTable * table, Vector * v);
// Add [<n>] row(s) [matching row(s) <row range>]
void gtable_addRows(GTable * table, Vector * v);
// Delete Row(s) [<row range>]
void gtable_deleteRows(GTable * table, Vector * v);
// Insert [<n>] Row(s) at <i> [matching row(s) <row range>]
void gtable_insertRows(GTable * table, Vector * v);

bool gtable_setValue(GTable * table, int row, int col, String * value);
bool gtable_setIntValue(GTable * table, int row, int col, double value);
bool gtable_validRow(GTable * table, String * row, int * start, int * finish);
int gtable_validCol(GTable * table, String * col);

void gtable_print(GTable * table);

#endif
