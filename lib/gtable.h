#ifndef __GTABLE_H
#define __GTABLE_H
/***********************************************
*  Header for Graphical tables
*  Command line interface for modifying tables
************************************************/

#include "table.h"
#include "basicTypes.h"
#include <stdarg.h>

typedef struct {
   Table * table;
   int * colWidths;
   int * colTypes;
   void * defaults; // the default value for rows
} GTable;

// ... = basic types
GTable * gtable_new(FreeFunc freeFunc, int rows, int cols, ...);

vodi gtable_destroy(GTable * table);

// ... = default values for row
void gtable_setDefaults(GTable * table, ...);

// ... = list of strings
void gtable_addHeader(Gtable * table, ...);

void gtable_setColWidth(GTable * table, int col, int width);

void gtable_processInput(GTable * table, String * input);

void gtable_print(GTable * table);

#endif
