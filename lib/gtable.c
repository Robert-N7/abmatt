/*******************************************
*   implementation for graphical tables
*******************************************/
#include "gtable.h"
#include <stdlib.h>
#include "table.h"
#include "basicTypes.h"
const char * GTABLE_SET = "Usage: Set <column> [<row range>] to <val> [incrementing [by <x>]]\n";
const char * GTABLE_SWAP = "Usage: Swap rows <row range> and <row range>\n";
const char * GTABLE_REPLACE = "Usage: Replace row(s) <row range> with row(s) <row range>\n";
const char * GTABLE_ADD = "Usage: Add [<n>] row(s) [matching row(s) <row range>]\n";
const char * GTABLE_DELETE = "Usage: Delete row(s) [<row range>]\n";
const char * GTABLE_INSERT = "Usage: Insert [<n>] Row(s) at <i> [matching row(s) <row range>]\n";
const char * GTABLE_UNKNOWNPARAM = "Unknown parameter '%s', expected '%s'\n";
const char * GTABLE_NOTENOUGHPARAMS = "'%s': Not enough parameters\n";
const char * GTABLE_NOTANUMBER = "'%s' is not a number.\n";
const char * GTABLE_NEGATIVENUMBER = "'%s': Must not be negative\n";

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
   Vector * v = strc_split(input, " ");
   if(!v) {
      fprintf(stderr, "%s: Not enough parameters", input->str);
      return;
   }
   String * first = vector_get(v, 0);
   // Set <column> [<row range>] to <val> [incrementing [by <x>]]
   if(strc_eq_ignore_case(first, "Set")) {
      gtable_set(table, v);
   }
   // Swap Rows <n> and <m>
   else if(strc_eq_ignore_case(first, "Swap")) {
      gtable_swapRows(table, v);
   }
   // Replace row(s) <row range> with row(s) <row range> [columns <col range>]
   else if(strc_eq_ignore_case(first, "Replace")) {
      gtable_replaceRows(table, v);
   } else if(!table->isFixedSize) {
      // Add [<n>] Row(s) [matching row <m>]
      if(strc_eq_ignore_case(first, "Add")) {
         gtable_addRows(table, v);
      }
      // Delete Row(s) [<row range>]
      else if(strc_eq_ignore_case(first, "Delete")) {
         gtable_deleteRows(table, v);
      }
      // Insert [<n>] Row(s) at <i>
      else if(strc_eq_ignore_case(first, "Insert")) {
         gtable_insertRows(table, v);
      }
   }
   vector_destroy(v);
}

// Set <column> [<row range>] to <val> [incrementing [by <x>]] [advancing by <y>]
void gtable_set(GTable * table, Vector * input) {
   if(input->size < 4) {
      fprintf(stderr, GTABLE_NOTENOUGHPARAMS, "Set");
      printf(GTABLE_SET);
      return;
   }
   String * s1 = vector_get(input, 1);
   int col = gtable_validCol(table, s1), start = 0, end = table_rowCount(table->table) - 1, i = 2, increment = 0, advancing = 0;
   if(col < 0)
      return;
   String * s2 = vector_get(input, i++);
   if(!strc_eq_ignore_case(s2, "to")) {
      // try row range
      if(!gtable_validRow(table, s2, &start, &end)) {
         printf(GTABLE_SET);
         return;
      }
      s1 = vector_get(input, i++);
      if(strc_eq_ignore_case( s1, "to"))
         ++i;
   } else
      ++i;
   if(!s1 = vector_get(input, i++)) {
      fprintf(stderr, GTABLE_NOTENOUGHPARAMS, "Set");
      printf(GTABLE_SET);
      return;
   }
   while(s2 = vector_get(input, i++)) {
      if(strc_in_ignore_case(s2, "increment", 0)) {

         if(s2 = vector_get(input, i++))
            if(!(increment = atoi(s2->str)) && (s2 = vector_get(input, i++)))
               increment = atoi(s2->str);
      }
      else if(strc_in_ignore_case(s2, "advanc", 0) == 0) {
         if(s2 = vector_get(input, i++))
            if(!(advancing = atoi(s2->str)) && (s2 = vector_get(input, i++)))
               advancing = atoi(s2->str);
      }
   }
   if(!advancing)
      ++advancing;
   if(increment) {
      if(!bt_isnum(table->colTypes[col])) {
         fprintf(stderr, "Unable to increment, Column %d is not numeric\n", col);
         return;
      }
      double db;
      if(!bt_convert_double(s1->str, &db)) {
         fprintf(stderr, "%s not a number\n", s1->str);
      } else
         for(int j = start; j <= finish; j += advancing, db += increment)
            gtable_setIntValue(table, j, col, db);
   } else
      for(int j = start; j < finish; j += advancing) {
         gtable_setValue(table, j, col, s1);
      }
}

// Swap Rows <row range> and <row range>
void gtable_swapRows(GTable * table, Vector * v) {
   if(v->size < 5) {
      fprintf(GTABLE_NOTENOUGHPARAMS, "Swap");
      printf(GTABLE_SWAP);
      return;
   }
   int i = 1, nstart, nend, mstart, mend;
   String * s = vector_get(v, i++), *sr1;
   if(!strc_in_ignore_case(s, "row") < 0) {
      fprintf(GTABLE_UNKNOWNPARAM, s->str, "rows");
      printf(GTABLE_SWAP);
      return;
   }
   sr1 = vector_get(v, i++);
   if(!gtable_validRow(table, s->str, &nstart, &nend) {
      printf(GTABLE_SWAP);
   }
   s = vector_get(v, i++);
   if(!strc_eq_ignore_case(s, "and") && !strc_eq_ignore_case(s, "with")) {
      fprintf(stderr, GTABLE_UNKNOWNPARAM, s->str, "and");
      printf(GTABLE_SWAP);
      return;
   }
   s = vector_get(v, i);
   if(!gtable_validRow(table, s->str, &mstart, &mend)) {
      printf(GTABLE_SWAP);
      return;
   }
   // check if the ranges match up
   if(mend - mstart != nend - nstart) {
      fprintf("Swap: Row range '%s' and '%s' are different size\n", sr1->str, s->str);
      return;
   }
   if(nstart < mstart && mstart < nend || nstart >= mstart && nstart < mend) {
      fprintf("Swap: Row ranges '%s' and '%s' overlap!\n", sr1->str, s->str);
      return;
   }
   // now perform swap
   for(; nstart < nend; nstart++, mstart++) {
      table_swapRows(table->table, nstart, mstart);
   }
}

// Replace row(s) <row range> with row(s) <row range> [columns <col range>]
void gtable_replaceRows(GTable * table, Vector * v) {
   if(v->size < 6) {
      fprintf(stderr, GTABLE_NOTENOUGHPARAMS, "Replace");
      printf(GTABLE_REPLACE);
      return;
   }
   int i = 1, nstart, nend, mstart, mend, colstart = 0, colend = table->table->columns;
   String * s1 = vector_get(v, i++), *s2;
   if(strc_in_ignore_case(s1, "row", 0) < 0) {
      fprintf(stderr, GTABLE_UNKNOWNPARAM, s1->str, "rows");
      printf(GTABLE_REPLACE);
      return;
   }
   s2 = vector_get(v, i++);
   if(!gtable_validRow(table, s2, &nstart, &nend)) {
      printf(GTABLE_REPLACE);
      return;
   }
   s1 = vector_get(v, i++);
   if(strc_eq_ignore_case(s1, "with", 0) < 0) {
      fprintf(stderr, GTABLE_UNKNOWNPARAM, s1->str, "with");
      printf(GTABLE_REPLACE);
      return;
   }
   s1 = vector_get(v, i++);
   if(strc_in_ignore_case(s1, "row", 0) < 0) {
      fprintf(stderr, GTABLE_UNKNOWNPARAM, s1->str, "rows");
      printf(GTABLE_REPLACE);
      return;
   }
   s1 = vector_get(v, i++);
   if(!gtable_validRow(table, s1->str, &mstart, &mend)) {
      printf(GTABLE_REPLACE);
      return;
   }
   if(s1 = vector_get(v, i++)) {
      if(strc_in_ignore_case(s1, "column", 0) < 0) {
         fprintf(stderr, GTABLE_UNKNOWNPARAM, s1->str, "columns");
         printf(GTABLE_REPLACE);
         return;
      }
      if(!s1 = vector_get(v, i++)) {
         fprintf(stderr, "Missing columns range parameter.\n");
         printf(GTABLE_REPLACE);
         return;
      }
      if(!gtable_validCol(table, s1)) {
         printf(GTABLE_REPLACE);
         return;
      }
   }
   Range * rng = table_getRange(table->table, mstart, colStart, mend, colend);
   table_pasteRange(table->table, rng, nstart, nend);
   table_freeRange(rng);
}

// Add [<n>] row(s) [matching row(s) <row range>]
void gtable_addRows(GTable * table, Vector * v) {
   if(v->length < 2) {
      fprintf(stderr, GTABLE_NOTENOUGHPARAMS, "Add");
      printf("%s", GTABLE_ADD);
      return;
   }
   int i = 1, numRows = 0, matchBegin = -1, matchEnd;
   String * s1 = vector_get(v, i++);
   if((strc_in_ignore_case(s1, "row", 0) < 0))
      numRows = 1;
   else if(!bt_convert_int(s1->str, &numRows)) {
      fprintf(stderr, GTABLE_NOTANUMBER, s1->str);
      printf(GTABLE_ADD);
      return;
   } else if(numRows <= 0) {
      fprintf(stderr, GTABLE_NEGATIVENUMBER, s1->str);
      printf(GTABLE_ADD);
      return;
   } else {
      if(s1 = vector_get(v, i++))
         if(strc_in_ignore_case(s1, "row", 0) < 0) {
            fprintf(stderr, GTABLE_UNKNOWNPARAM, s1->str, "rows");
            printf("%s", GTABLE_ADD);
            return;
         }
   }
   if(s1 = vector_get(v, i++)) {
      if(!str_eq_ignore_case(s1, "matching")) {
         fprintf(stderr, GTABLE_UNKNOWNPARAM, s1->str, "matching");
         printf("%s", GTABLE_ADD);
         return;
      }
      s1 = vector_get(v, i++);
      if(strc_in_ignore_case(s1, "row", 0) < 0) {
         fprintf(stderr, GTABLE_UNKNOWNPARAM, s1->str, "rows");
         printf("%s", GTABLE_ADD);
         return;
      }
      s1 = vector_get(v, i++);
      if(!gtable_validRow(table, s1, &matchBegin, &matchEnd)) {
         printf("%s", GTABLE_ADD);
         return;
      }
   }
   int colBegin = 0, colEnd = table->table->columns, startRow = table_rowCount(table->table);
   for(int i = 0; i < numRows; i++) {
      table_addEmptyRow(table->table);
   }
   if(matchBegin >= 0) { // then use matching
      Range * rng = table_getRange(table->table, matchBegin, colBegin, matchEnd, colEnd);
      table_pasteRange(table->table, rng, startRow, startRow + numRows);
      table_freeRange(rng);
   }
}

// Delete Row(s) [<row range>]
void gtable_deleteRows(GTable * table, Vector * v) {
   if(v->length < 2) {
      fprintf(stderr, GTABLE_NOTENOUGHPARAMS, "Delete");
      printf(GTABLE_DELETE);
      return;
   }
   int i = 1, start, finish = table_rowCount(table->table);
   String * s1 = vector_get(v, i++);
   if(strc_in_ignore_case(s1->str, "row", 0)  < 0) {
      fprintf(stderr, GTABLE_UNKNOWNPARAM, s1->str, "rows");
      printf(GTABLE_DELETE);
      return;
   }
   if(s1 = vector_get(v, i++)) {
      if(!gtable_validRow(table, s1, &start, &finish)) {
         printf(GTABLE_DELETE);
         return;
      }
   } else
      start = finish - 1;
   for(int j = start; j < finish; j++) {
      table_deleteRow(table->table, j);
   }
}

// Insert [<n>] Row(s) at <i> [matching row(s) <row range>]
void gtable_insertRows(GTable * table, Vector * v) {
   if(v->length < 4) {
      fprintf(stderr, GTABLE_NOTENOUGHPARAMS, "Insert");
      printf(GTABLE_INSERT);
      return;
   }
   int i = 1, numRows, atIndex, atEnd, matchBegin = -1, matchEnd;
   String * s1 = vector_get(v, i++);
   if(strc_in_ignore_case(s1->str, "row", 0) < 0) {
      if(!bt_convert_int(s1->str, &numRows)) {
         fprintf(stderr, GTABLE_NOTANUMBER, s1->str);
         printf(GTABLE_INSERT);
         return;
      } else if(numRows <= 0) {
         fprintf(stderr, GTABLE_NEGATIVENUMBER, s1->str);
         printf(GTABLE_INSERT);
         return;
      }
      s1 = vector_get(v, i++);
      if(strc_in_ignore_case(s1->str, "row", 0) < 0) {
         fprintf(stderr, GTABLE_UNKNOWNPARAM, s1->str);
         printf(GTABLE_INSERT);
         return;
      }
   } else
      numRows = 1;
   s1 = vector_get(v, i++);
   if(!strc_eq_ignore_case(s1, "at")) {
      fprintf(stderr, GTABLE_UNKNOWNPARAM, s1->str, "at");
      printf(GTABLE_INSERT);
      return;
   }
   if(!(s1 = vector_get(v, i++)) {
      fprintf(stderr, GTABLE_NOTENOUGHPARAMS, "Insert");
      printf(GTABLE_INSERT);
      return;
   }
   if(!gtable_validRow(table, s1, &atIndex, &atEnd)) {
      printf(GTABLE_INSERT);
      return;
   }
   if(s1 = vector_get(v, i++)) {
      // matching
      if(!str_eq_ignore_case(s1, "matching")) {
         fprintf(stderr, GTABLE_UNKNOWNPARAM, s1->str, "matching" );
         printf(GTABLE_INSERT);
         return;
      }
      if(!(s1 = vector_get(v, i++)) || strc_in_ignore_case(s1->str, "row", 0) < 0) {
         fprintf(stderr, "Expected 'rows'.\n");
         printf(GTABLE_INSERT);
         return;
      }
      if(!(s1 = vector_get(v, i++)) || !gtable_validRow(table, s1, &matchBegin, &matchEnd)) {
         printf(GTABLE_INSERT);
         return;
      }
   }
   table_insertRows(table->table, atIndex, numRows);
   if(matchBegin >= 0) {
      // then put in the matching values
      Range * rng = table_getRange(table->table, matchBegin, 0, matchEnd, table->table->columns);
      table_pasteRange(table->table, rng, atIndex, atIndex + numRows);
      table_freeRange(rng);
   }
}

bool gtable_setValue(GTable * table, int row, int col, String * value) {
   // check if it's correct type
   bt_Type expected = table->colTypes[col];
   if(expected == bt_UInt32) {
      uint32_t val;
      if(bt_convert_int(value->str, &val)) {
         table_set(table->table, row, col, &val);
         return true;
      }
   } else if(expected == bt_UInt16) {
      uint16_t val;
      if(bt_convert_int(value->str, &val)) {
         table_set(table->table, row, col, &val);
         *intVal = val;
         return true;
      }
   } else if(expected == bt_UInt8) {
      uint8_t val;
      if(bt_convert_int(value->str, &val)) {
         table_set(table->table, row, col, &val);
         *intVal = val;
         return true;
      }
   } else if(expected == bt_UInt64) {
      uint64_t val;
      if(bt_convert_int(value->str, &val)) {
         table_set(table->table, row, col, &val);
         *intVal = val;
         return true;
      }
   } else if(expected == bt_Int32) {
      int32_t val;
      if(bt_convert_int(value->str, &val)) {
         table_set(table->table, row, col, &val);
         *intVal = val;
         return true;
      }
   } else if(expected == bt_Int16) {
      int16_t val;
      if(bt_convert_int(value->str, &val)) {
         table_set(table->table, row, col, &val);
         *intVal = val;
         return true;
      }
   } else if(expected == bt_Int8) {
      int8_t val;
      if(bt_convert_int(value->str, &val)) {
         table_set(table->table, row, col, &val);
         *intVal = val;
         return true;
      }
   } else if(expected == bt_Int64) {
      int64_t val;
      if(bt_convert_int(value->str, &val)) {
         table_set(table->table, row, col, &val);
         *intVal = val;
         return true;
      }
   } else if(expected == bt_Float32) {
      float val;
      if(bt_convert_float(value->str, &val)) {
         table_set(table->table, row, col, &val);
         *intVal = val;
         return true;
      }
   } else if(expected == bt_Double64) {
      double val;
      if(bt_convert_double(value->str, &val)) {
         table_set(table->table, row, col, &val);
         *intVal = val;
         return true;
      }
   } else if(expected == bt_Bool1) {
      bool val;
      if(bt_convert_bool(value->str, &val)) {
         table_set(table->table, row, col, &val);
         *intVal = val;
         return true;
      }
   } else if(bt_isChar(expected)) {
      // no conversion necessary - must be correct size
      if(bt_size(expected) == value->str->length * 8) {
         table->set(table->table, row, col, value->str);
         return true;
      }
   }
   fprintf(stderr, "Incorrect data type '%s' for table column %d\n", value->str, col);
   return false;
}

bool gtable_setIntValue(GTable * table, int row, int col, double value) {
   // check if it's correct type
   bt_Type expected = table->colTypes[col];
   if(expected == bt_UInt32) {
      uint32_t val = value;
      table_set(table->table, row, col, &val);
      return true;
   } else if(expected == bt_UInt16) {
      uint16_t val = value;
      table_set(table->table, row, col, &val);
      return true;
   } else if(expected == bt_UInt8) {
      uint8_t val = value;
         table_set(table->table, row, col, &val);
         return true;
   } else if(expected == bt_UInt64) {
      uint64_t val = value;
         table_set(table->table, row, col, &val);
         return true;
   } else if(expected == bt_Int32) {
      int32_t val = value;
         table_set(table->table, row, col, &val);
         return true;
   } else if(expected == bt_Int16) {
      int16_t val = value;
         table_set(table->table, row, col, &val);
         return true;
   } else if(expected == bt_Int8) {
      int8_t val = value;
         table_set(table->table, row, col, &val);
         return true;
   } else if(expected == bt_Int64) {
      int64_t val = value;
         table_set(table->table, row, col, &val);
         return true;
   } else if(expected == bt_Float32) {
      float val = value;
         table_set(table->table, row, col, &val);
         return true;
   } else if(expected == bt_Double64) {
      double val = value;
         table_set(table->table, row, col, &val);
         return true;
   }
   fprintf(stderr, "Incorrect data type '%s' for table column %d\n", value->str, col);
   return false;
}


bool gtable_validRow(GTable * table, String * row, int * start, int * finish) {
   int r, pos;
   bool valid = true;
   if((pos = strc_in(row, "-", 0)) != STR_NOT_FOUND) { // range?
      String * strart = str_slice(row, 0, pos);
      String * strend = str_slice(row, pos + 1, STR_END);
      if(!strart || !bt_convert_int(strart->str, start)) {
         valid = false;
      } else if(!strend || !bt_convert_int(strend->str, finish)) {
         valid = false;
      }
      str_free(strart);
      str_free(strend);
   } else if(!bt_convert_int(row->str, start))
      valid = false;
    else // not range and converted
      *finish = *start;
   if((r = table_rowCount(table->table)) <= *start || r <= *finish || *start < 0 || *finish < 0) {
      valid = false;
   }
   if(!valid) {
      fprintf(stderr, "Not a valid row range: %s\n", row->str);
   }
   *finish += 1;
   return valid;
}

bool gtable_validCol(GTable * table, String * col, int * start, int * finish) {
   int c, pos;
   bool valid = true;
   if((pos = strc_in(col, "-", 0)) != STR_NOT_FOUND) { // range?
      String * strart = str_slice(col, 0, pos);
      String * strend = str_slice(col, pos + 1, STR_END);
      if(!strart || !bt_convert_int(strart->str, start)) {
         valid = false;
      } else if(!strend || !bt_convert_int(strend->str, finish)) {
         valid = false;
      }
      str_free(strart);
      str_free(strend);
   } else if(!bt_convert_int(row->str, start))
      valid = false;
    else // not range and converted
      *finish = *start;
   if((c = table_colCount(table->table)) <= *start || c <= *finish || *start < 0 || *finish < 0) {
      valid = false;
   }
   if(!valid) {
      fprintf(stderr, "Not a valid column range: %s\n", row->str);
   }
   *finish += 1;
   return valid;
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

void gtable_addRow(Gtable * table, ...) {
   va_list list;
   va_start(list, table);
   table_vaddRow(table->table, list);
   va_end(list);
}
