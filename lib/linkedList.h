/**********************************************
* Robert Nelson
*   Linked List implementation
***********************************************/
#ifndef __List_H
#define __List_H

typedef void (*freeFunction)(void *);
typedef char * (*strFunction)(void *);

// Node Data structure
typedef struct _listNode {
  void * data;
  struct _listNode * next;
} ListNode;

typedef struct {
  freeFunction freeFunc;
  ListNode *head;
  ListNode *tail;
  int elementSize;
  int length;
} List;

// list_new
List * list_new(int elementSize, freeFunction freeFunc);

// list copy
List * list_copy(List * original);

// list join, joins the two lists
// returns a pointer to original on success and frees the new
// Join fails if the lists have different free functions
List * list_join(List * original, List * new);

// list_destroy
void list_destroy(List * list);

// Adds a node to beginning of list
void * list_prepend(List * list, const void * element);

// Adds a node to end of list
void * list_append(List * list, const void * element);

// Size
int list_size(List * list);

// Head
ListNode * list_head(List * list);

// Tail
ListNode * list_tail(List * list);

// Get the next element
ListNode * list_next(List * list, ListNode * current);

// list remove, returns an element from list (must be freed)
void * list_remove(List * list, void * element);

// removes an element from the list
void list_delete_node(List * list, ListNode ** node, ListNode ** prev);

// list delete element
int list_delete(List * list, void * element);

// list find
ListNode * list_find(List * list, void * element);

// list index - listnodes must be pass by reference to use
void * list_index(List * list, int index, ListNode ** node, ListNode ** prev);

// Push
void * list_push(List * list, const void * element);

// Pop
void * list_pop(List * list, int index);

// Get
void * list_get(List * list, int index);

// Set
void * list_set(List * list, int index, void * value);

#endif
