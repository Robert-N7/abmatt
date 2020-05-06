/*****************************************************************
* Basic Types implementation
******************************************************************/
#include "basicTypes.h"
#include <stdlib.h>
#include "stringUtil.h"

bool bt_convert_bool(char * str, bool * retBool) {
  if(cstr_eq_ignore_case(str, bt_TRUE)) {
    *retBool = true;
  } else if(cstr_eq_ignore_case(str, bt_FALSE))
      *retBool = false;
  else
    return false;
  return true;
}

bool bt_convert_int(char * str, long int * retInt) {
  char * ptr;
  *retInt = strtol(str, &ptr, 0);
  return *ptr == '\0' && *str != '\0';
}

bool bt_convert_float(char * str, float * retFloat) {
  char * ptr;
  *retFloat = strtof(str, &ptr);
  return *ptr == '\0' && *str != '\0';
}

bool bt_convert_double(char * str, double * retDouble) {
  char * ptr;
  *retFloat = strtod(str, &ptr);
  return *ptr == '\0' && *str != '\0';
}
