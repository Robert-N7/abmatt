#ifndef __BASICTYPE_H
#define __BASICTYPE_H
/********************************************************
*  Basic type operations library
*********************************************************/
#define bt_UInt8 0x08
#define bt_UInt16 0x10
#define bt_UInt32 0x20
#define bt_UInt64 0x40
#define bt_Int8 0x108
#define bt_Int16 0x110
#define bt_Int32 0x120
#define bt_Int64 0x140
#define bt_Float32 0x220
#define bt_Double64 0x240
#define bt_Double128 0x280
#define bt_Byte8 0x408
#define bt_Nibble4 0x804
#define bt_Bool1 0xf01
#define bt_TRUE "TRUE"
#define bt_FALSE "FALSE"
typedef int bt_Type;

#include <stdbool.h>
#include "str.h"

bool bt_convert_bool(char * str, bool * retBool);
bool bt_convert_int(char * str, long int * retInt);
bool bt_convert_float(char * str, float * retFloat);
bool bt_convert_double(char * str, double * retDouble);
String * bt_toString(bt_Type type, void * data, char * precision);
bt_Type bt_setByteSize(short size) { return 0x04ff & size; } // 255 max

int bt_size(bt_Type type) {   return type & 0x00ff;   }
bool bt_isInt(bt_Type type) { return !(type & 0xfe00); }
bool bt_isFloat(bt_Type type) { return type & 0x0200; }
bool bt_isnum(bt_Type type) { return !(type & 0xfc00); }
bool bt_isChar(bt_Type type) { return type & 0x0400; }
bool bt_isBool(bt_Type type) { return type & 0x0f00; }
#endif
