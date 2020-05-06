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
#define bt_Byte8 0x308
#define bt_Nibble4 0x04
#define bt_Bool1 0x01
typedef int BType;


#include <stdbool.h>

bool btype_is_int(char * str) {

}

bool btype_is_float(char * str) {

}

int btype_size(BType type) {   return type & 0x00ff;   }
#endif
