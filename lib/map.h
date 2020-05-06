#ifndef Map_H
#define Map_H
/**************************************************
* Map Header file for hash maps
***************************************************/

// Node
typedef struct _mapNode {
  char * key;
  void * value;
  struct _mapNode * next;
} MapNode;

typedef void (*Map_freefunc)(void *);

// Map
typedef struct _map {
  Map_freefunc freefunc; // For freeing data on destroy
  MapNode ** table;     // map table
  unsigned int elementSize;    // capacity of each value (use 0 for strings)
  unsigned int capacity;         // capacity of map
  unsigned int size;           // number of elements
} Map;

// Map iterator
MapNode * map_iterator(Map * m);

// Map next, used with map iterator
MapNode * map_next(Map * m, MapNode * mn);

// constructor
Map * map_new(int capacity, int elementSize, Map_freefunc freeFunc);

// copys map with new capacity
Map * map_copy(Map * m, int capacity);

// frees input map and returns a new map to fit current size
Map * map_update(Map *m);

// destructor
void map_destroy(Map * m);

// hashes the key
unsigned long map_hash(Map * m, const char * key);

// gets the value in the map, no allocation
void * map_key(Map * m, const char * key);

// get value from map
void * map_get(Map * m, const char * key);

// set key, value pair
void * map_set(Map *m, const char * key, const void * value);

// map count
int map_count(Map * map);
#endif
