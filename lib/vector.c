/***********************************************************
*  Vector
************************************************************/
#include "vector.h"
#include <stdlib.h>
#include <string.h>

Vector * vector_new(int capacity, int elementSize, FreeFunc freeFunc) {
   Vector * new = malloc(sizeof(Vector));
   new->capacity = capacity;
   new->freeFunc = freeFunc;
   new->elementSize = elementSize;
   new->size = 0;
   new->data = malloc(capacity);
   return new;
}

void vector_append(Vector * original, const Vector * newData) {
   if(original->capacity < original->size + newData->size) {
      vector_resize(original, original->size + newData->size * 2);
   }
   // they better be same size data
   memcpy(original->data + original->size * original->elementSize, newData->data, newData->size * original->elementSize);
   original->size += newData->size;
}

void * vector_get(Vector * vector, int index) {
   return vector->data + index * vector->elementSize;
}

void vector_set(Vector * vector, int index, void * data) {
   memcpy(vector->data + index * vector->elementSize, data, vector->elementSize);
}

void vector_swap(Vector * vector, int index1, int index2) {
   void * tmp = malloc(vector->elementSize);
   void * pos1 = vector_get(vector, index1);
   void * pos2 = vector_get(vector, index2);
   memcpy(tmp, pos1, vector->elementSize);
   memcpy(pos1, pos2, vector->elementSize);
   memcpy(pos2, tmp, vector->elementSize);
   free(tmp);
}

Vector * vector_copy(Vector * vector) {
   Vector * vec = vector_new(vector->capacity, vector->elementSize, vector->freeFunc);
   memcpy(vec->data, vector->data, vector->elementSize * vector->size);
   vec->size = vector->size;
   return vec;
}

void vector_resize(Vector * vector, int newCapacity) {
   vector->capacity = newCapacity;
   void * ptr = realloc(vector->data, newCapacity);
   if(!ptr) {
      ptr = malloc(vector->capacity * vector->elementSize);
      memcpy(ptr, vector->data, vector->elementSize * vector->size);
      free(vector->data);
      vector->data = ptr;
   }
}

void vector_destroy(Vector * vector) {
   if(vector->freeFunc)
   for(int i = 0; i < vector->size; i++) {
      vector->freeFunc(vector->data + vector->elementSize * i);
   }
   free(vector->data);
   free(vector);
}

void vector_push(Vector * vector, void * data) {
   if(vector->size >= vector->capacity) {
      vector_resize(vector, vector->capacity * 2);
   }
   memcpy(vector->data + vector->elementSize * vector->size, data, vector->elementSize);
   vector->size += 1;
}

bool vector_pop(Vector * vector) {
   if(vector->size) {
      vector->size -= 1;
      if(vector->freeFunc)
         vector->freeFunc(vector->data + vector->elementSize * vector->size);
      return true;
   }
   return false;
}

void vector_clear(Vector * vector) {
   if(vector->freeFunc)
      for(int i = 0; i < vector->elementSize; i++)
         vector->freeFunc(vector->data + vector->elementSize * i);
   vector->size = 0;
}

void vector_delete(Vector * vector, int index) {
   if(vector->freeFunc)
      vector->freeFunc(vector->data + index * vector->elementSize);
   int trailing = vector->size - index - 1; // number of trailing elements
   if(trailing)
      memcpy(vector->data + index * vector->elementSize, vector->data + (index + 1), trailing * vector->elementSize);
   vector->size -= 1;
}

void vector_deleteRange(Vector * vector, int start, int finish) {
   if(vector->freeFunc) {
      for(int i = start; i < finish; i++)
         vector->freeFunc(vector->data + i * vector->elementSize);
   }
   int trailing = vector->size - finish;
   int numElements = finish - start;
   if(trailing) {
      memcpy(vector->data + start * vector->elementSize, vector->data + finish * vector->elementSize, trailing * vector->elementSize);
   }
   vector->size -= numElements;
}

void vector_insert(Vector * vector, int index, void * data) {
   if(vector->size >= vector->capacity)
      vector_resize(vector, vector->capacity * 2);
   // since we don't want to overwrite data.. start at the end
   int i = vector->size, eSize = vector->elementSize;
   for(void * ptr = vector->data + i * eSize; i > index; ptr -= eSize, i--) {
      memcpy(ptr, ptr - eSize, eSize);
   }
   // now we made room...
   memcpy(vector->data + eSize * index, data, eSize);
   vector->size += 1;
}
