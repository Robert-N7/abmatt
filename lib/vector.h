#ifndef __VECTOR_H
#define __VECTOR_H
#include <stdbool.h>
/***********************************************************
*  Vector header
************************************************************/
typedef void (*FreeFunc)(void *);

typedef struct {
   int size;
   int elementSize;
   int capacity;
   FreeFunc freeFunc;
   void * data;
} Vector;

Vector * vector_new(int capacity, int elementSize, FreeFunc freeFunc);

Vector * vector_copy(Vector * vector);
Vector * vector_slice(Vector * vector, int start, int end);

void vector_append(Vector * original, const Vector * newData);

void * vector_get(Vector * vector, int index);
// retrieves the item assuming it to be a pointer
void * vector_getp(Vector * vector, int index);

void vector_set(Vector * vector, int index, void * data);

void vector_swap(Vector * vector, int index1, int index2);

void vector_resize(Vector * vector, int newCapacity);

void vector_destroy(Vector * vector);

void vector_push(Vector * vector, void * data);

bool vector_pop(Vector * vector);

void vector_clear(Vector * vector);

// These operations are not very optimal for vectors
void vector_delete(Vector * vector, int index);

// deletes from [start, finish)
void vector_deleteRange(Vector * vector, int start, int finish);

// O(n) worst case
void vector_insert(Vector * vector, int index, void * data);

int vector_size(Vector * vector);
#endif
