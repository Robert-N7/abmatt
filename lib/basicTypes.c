/*****************************************************************
* Basic Types implementation
******************************************************************/
#include "basicTypes.h"
#include <stdlib.h>
#include "str.h"
#include "stringUtil.h"
#include <stdio.h>
#include <stdint.h>

bool bt_convert_bool(String * str, bool * retBool) {
  if(cstr_eq_ignore_case(str->str, bt_TRUE)) {
    *retBool = true;
  } else if(cstr_eq_ignore_case(str->str, bt_FALSE))
      *retBool = false;
  else
    return false;
  return true;
}

bool bt_convert_int(String * str, long int * retInt) {
  char * ptr;
  *retInt = strtol(str->str, &ptr, 0);
  return *ptr == '\0' && *str != '\0';
}

bool bt_convert_float(String * str, float * retFloat) {
  char * ptr;
  *retFloat = strtof(str->str, &ptr);
  return *ptr == '\0' && *str != '\0';
}

bool bt_convert_double(String * str, double * retDouble) {
  char * ptr;
  *retFloat = strtod(str->str, &ptr);
  return *ptr == '\0' && *str != '\0';
}


String * bt_toString(bt_Type type, void * data, char * precision) {
  String * str = malloc(sizeof(String));
  char fmtBuffer[10];
  int i = 0;
  fmtBuffer[i++] = '%';
  for(char * c = precision; *c; c++)
    fmtBuffer[i++] = *c;
  switch(type) {
      case bt_UInt32:
        fmtBuffer[i++] = 'l';
        fmtBuffer[i++] = 'u';
        fmtBuffer[i++] = '\0';
        str->len = str->capacity =  asprintf(&str->str, fmtBuffer, (uint32_t) data);
        break;
      case bt_Int32:
        fmtBuffer[i++] = 'd';
        fmtBuffer[i++] = '\0';
        str->len = str->capacity =  asprintf(&str->str, fmtBuffer, (uint32_t) data);
        break;
      case bt_UInt64:
        fmtBuffer[i++] = 'l';
        fmtBuffer[i++] = 'u';
        fmtBuffer[i++] = '\0';
        str->len = str->capacity =  asprintf(&str->str, fmtBuffer, (uint64_t) data);
        break;
      case bt_Int64:
        fmtBuffer[i++] = 'l';
        fmtBuffer[i++] = '\0';
        str->len = str->capacity =  asprintf(&str->str, fmtBuffer, (int64_t) data);
        break;
      case bt_UInt16:
        fmtBuffer[i++] = 'h';
        fmtBuffer[i++] = 'u';
        fmtBuffer[i++] = '\0';
        str->len = str->capacity =  asprintf(&str->str, fmtBuffer, (uint16_t) data);
        break;
      case bt_Int16:
        fmtBuffer[i++] = 'h';
        fmtBuffer[i++] = 'i';
        fmtBuffer[i++] = '\0';
        str->len = str->capacity =  asprintf(&str->str, fmtBuffer, (int16_t) data);
        break;
      case bt_Float32:
        fmtBuffer[i++] = 'f';
        fmtBuffer[i++] = '\0';
        str->len = str->capacity =  asprintf(&str->str, fmtBuffer, (float) data);
        break;
      case bt_Double64:
        fmtBuffer[i++] = 'E';
        fmtBuffer[i++] = '\0';
        str->len = str->capacity =  asprintf(&str->str, fmtBuffer, (double) data);
        break;
      case bt_UInt8:
        fmtBuffer[i++] = 'h';
        fmtBuffer[i++] = 'u';
        fmtBuffer[i++] = '\0';
        str->len = str->capacity =  asprintf(&str->str, fmtBuffer, (uint8_t) data);
      break;
      case bt_Int8:
        fmtBuffer[i++] = 'h';
        fmtBuffer[i++] = 'i';
        fmtBuffer[i++] = '\0';
        str->len = str->capacity =  asprintf(&str->str, fmtBuffer, (int8_t) data);
        break;
      case bt_Double128:
        fmtBuffer[i++] = 'E';
        fmtBuffer[i++] = '\0';
        str->len = str->capacity =  asprintf(&str->str, fmtBuffer, (long double) data);
      break;
      case bt_Bool1:
        bool val = (bool) data;
        if(val) {
          fmtBuffer[--i] = 'T'
          fmtBuffer[i++] = 'r';
          fmtBuffer[i++] = 'u';
          fmtBuffer[i++] = 'e';
          fmtBuffer[i++] = '\0';
        } else {
          fmtBuffer[--i] = 'F'
          fmtBuffer[i++] = 'a';
          fmtBuffer[i++] = 'l';
          fmtBuffer[i++] = 's';
          fmtBuffer[i++] = 'e';
          fmtBuffer[i++] = '\0';
        }
        str->len = str->capacity =  asprintf(&str->str, fmtBuffer, (bool) data);
        break;
      default:
        fmtBuffer[i++] = 'X'; // hex
        str->len = str->capacity =  asprintf(&str->str, fmtBuffer, (char) data);
        break;
  }
  return str;
}
