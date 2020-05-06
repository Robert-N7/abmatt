#ifndef __GTABLE_H
#define __GTABLE_H
/***********************************************
*  Header for Graphical tables
*  Command line interface for modifying tables
************************************************/

#include "table.h"

typedef struct {
   Table * table;
   int * colWidths;
} GTable;



void gtable_print(GTable * table);

#endif
