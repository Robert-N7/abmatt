/****************************************************
* Map implementation
****************************************************/
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include "map.h"
#include "str.h"

// constructor
Map * map_new(int capacity, int elementSize, Map_freefunc freeFunc) {
  Map * m = malloc(sizeof(struct _map));
  m->capacity = capacity;
  m->freefunc = freeFunc;
  m->elementSize = elementSize;
  m->size = 0;
  MapNode ** table = malloc(sizeof(MapNode *) * capacity); // table array
  for(int i = 0; i < capacity; i++) {
    table[i] = NULL;
  }
  m->table = table;
  return m;
}

// copys map with new capacity
Map * map_copy(Map * m, int capacity) {
  Map * ret = map_new(capacity, m->elementSize, m->freefunc);
  for(MapNode * mn = map_iterator(m); mn; mn = mn->next)
    map_set(ret, mn->key, mn->value);
  return ret;
}

// copies map to fit current size destroying current
Map * map_update(Map *m) {
  Map * ret = map_copy(m, m->size * 5/4);
  map_destroy(m);
  return ret;
}

// destructor
void map_destroy(Map * m) {
  MapNode ** table = m->table;
  MapNode * mn, *nextmn;
  for(int i = 0; i < m->capacity; i++) { // destroy each  node list
    for(mn = table[i]; mn; mn = nextmn) {
      if(m->freefunc)
        m->freefunc(mn->value);  // free function for complex objects
      else
        free(mn->value);  // free value
      free(mn->key);  // free key
      nextmn = mn->next;
      free(mn);  // free node
    }
  }
  free(table); // free table
  free(m); // free this object
}

unsigned long map_hash(Map * m, const char * key) {
   unsigned long hash = 5381;
   int c;
   while (c = *key++)
      hash = (((hash << 5) + hash) + c) % m->capacity; /* hash * 33 + c */
   return hash % m->capacity;
}

// gets the value in the map, no allocation
void * map_key(Map * m, const char * key) {
   int code = map_hash(m, key);
   MapNode * mn = m->table[code]; // index into table
   while(mn) { // locate the key
       if(strcmp(key, mn->key) == 0) {
          return mn->value;
       }
       mn = mn->next;
   }
   return NULL;
}

// get value from map, allocating memory
void * map_get(Map * m, const String * key) {
   char * val;
   if(val = map_key(m, key)) {
      void * element = malloc(m->elementSize);
      memcpy(element, val, m->elementSize);
      return element;
   }
   return NULL;
}

// set key, value pair
void * map_set(Map *m, const char * key, const void * value) {
  int code = map_hash(m, key);
  MapNode *start = m->table[code], *temp, *prev = 0;
  // find the key or the end of list
  for(temp = start; temp; temp = temp->next) {
      if(strcmp(temp->key, key) == 0) {
        // found it
        if(value == NULL) { // Delete it
            if(m->freefunc)
              m->freefunc(temp->value);
            else
              free(temp->value);
            free(temp->key);
            if(prev)
              prev->next = temp->next;
            else // first element
              m->table[code] = temp->next;
            free(temp);
            m->size--;
            return NULL;
        }
        // else not null
        // otherwise same capacity data - free old data
        if(m->freefunc) {
          m->freefunc(temp->value);
          temp->value = malloc(m->elementSize);
        }
        memcpy(temp->value, value, m->elementSize); // copy new
        return temp->value;
      }
      prev = temp;
  }
  // Didn't find key in list - create it
  MapNode * newNode = malloc(sizeof(struct _mapNode));
  newNode->key = str(key);
  newNode->next = NULL; // set next to null since it's the last
  newNode->value = malloc(m->elementSize);
  memcpy(newNode->value, value, m->elementSize);
  m->size++;
  // hook up node
  if(prev)
    prev->next = newNode;
  else
    m->table[code] = newNode;
  return newNode->value;
}

// Map next for iterating through map, use with map iterater
MapNode * map_next(Map * m, MapNode * mn) {
   if(!mn)
      return NULL;
  if(mn->next)
    return mn->next;
  int index = map_hash(m, mn->key); // find where we're at
  for(int i = index + 1; i < m->capacity; i++) {
     if(m->table[i]) {
        return m->table[i];
     }
  }
  return NULL;
}

// Map iterator for iterating
MapNode * map_iterator(Map * m) {
  MapNode * iterater;
  for(int i = 0; i < m->capacity; i++) {
     if(iterater = m->table[i]) {
        return iterater;
     }
  }
  return NULL;
}

// map count
int map_count(Map * map) {
  int ret = 0;
  for(MapNode * mn = map_iterator(map); mn; mn = map_next(map, mn)) {
    ++ret;
  }
  return ret;
}
