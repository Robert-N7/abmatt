/****************************************************************
*  Dealing with BRRES files
*  Robert Nelson
*****************************************************************/
#include "brres.h"
#include "../lib/str.h"
#include "../lib/serialize.h"
#include "../lib/vector.h"
#include "../lib/linkedList.h"
#include "../lib/gtable.h"
#include "../lib/basicTypes.h"
BinTemplate * BRRES_TEMPLATE;


int main(int argc, char ** argv) {
   return 0;
}

void brres_template_init() {
   BinTemplate * t = bin_template_new("brres");
   bt_add(t, Byte, "magic", 4);
   bt_add(t, Int16, "bom", 1);
   bt_add(t, Int16, "padding", 1);
   bt_add(t, Int32, "filesize", 1);
   bt_add(t, Int16, "rootoffset", 1);
   bt_add(t, Int16, "numSections", 1);
   BinTemplate * root = bin_template_new("root");
   // header
   bt_add(t, Byte, "magic", 4);
   bt_add(t, Int32, "sectionLength", 1);
   BinTemplate * brresIndex = bin_template_new("brresIndex");
   // header
   bt_add(t, Int32, "length", 1);
   bt_add(t, Int32, "numGroup", 1);
   BinTemplate * brresIndexEntry = bin_template_new("brresIndexEntry");
   bt_add(t, Int16, "entryid", 1);
   bt_add(t, Int16, "leftIndex", 1);
   bt_add(t, Int16, "rightIndex", 1);
   bt_add(t, Int32, "namePointer", 1);
   bt_add(t, Int32, "dataPointer", 1);

}
