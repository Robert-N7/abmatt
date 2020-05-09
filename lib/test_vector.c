/**************************************************************
*   Robert Nelson
*  Vector test
***************************************************************/
#include "vector.h"
#include <stdio.h>
#include <stdlib.h>
#include "str.h"

int main() {
   Vector * v = vector_new(5, sizeof(int), 0);
   for(int i = 0; i < 20; i++) {
      vector_push(v, &i);
   }
   for(int i = 0, *j; i < 20; i++) {
      j = vector_get(v, i);
      if(*j != i) {
         printf("an error has occurred.\n");
      }
   }
   vector_destroy(v);
   v = vector_new(3, sizeof(String * ), str_freepointer);
   char buffer[2];
   buffer[1] = '\0';
   String * s;
   for(int i = 65; i < 124; i++) {
      buffer[0] = i;
      s = str(buffer);
      vector_push(v, &s);
   }
   for(int i = 0; i < v->size; i++) {
      s = *((String **) vector_get(v, i));
      str_print(s);
   }
   vector_destroy(v);
   return 0;
}
