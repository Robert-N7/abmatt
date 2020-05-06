/**********************************************
* Robert Nelson
*   Linked List implementation
***********************************************/
#include <stddef.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include "linkedList.h"

// list_new
List * list_new(int elementSize, freeFunction freeFunc) {
  List * list = malloc(sizeof(List));
  list->length = 0;
  list->elementSize = elementSize; // set to 0 to treat as list of strings
  list->head = NULL;
  list->tail = NULL;
  list->freeFunc = freeFunc; // For freeing complex data
  return list;
}

// list copy
List * list_copy(List * original) {
  List * r = list_new(original->elementSize, original->freeFunc);
  for(ListNode *ln = original->head; ln; ln = ln->next) {
    list_append(r, ln->data);
  }
  return r;
}

// list join, joins the two lists
// returns a pointer to original on success and frees the new
// Join fails if the lists have different free functions
List * list_join(List * original, List * new) {
  if(original->freeFunc != new->freeFunc) {

    return NULL;
  }
  if(new->elementSize != original->elementSize) {

    if(new->elementSize > original->elementSize)
      original->elementSize = new->elementSize;
  }
  ListNode * ln = original->tail;
  if(ln) { // list not empty?
    ln->next = new->head;
  } else {
    original->head = new->head;
  }
  if(new->tail)
    original->tail = new->tail;
  original->length += new->length;
  free(new); // free the new list - leaving the nodes intact
  return original;
}

// list_destroy
void list_destroy(List * list) {
  if(list) {
    ListNode * ln;
    while(list->head)
    {
      ln = list->head;
      list->head = ln->next; // Advance the head
      if(list->freeFunc) {
        list->freeFunc(ln->data);
      } else
        free(ln->data);
      free(ln);
    }
    free(list);
  }
}

// Adds a node to beginning of list
void * list_prepend(List * list, const void * element) {
  ListNode * node = malloc(sizeof(ListNode));
  node->data = malloc(list->elementSize); // allocate mem
  memcpy(node->data, element, list->elementSize); // copy the element
  node->next = list->head;
  list->head = node; // new head
  if(!list->tail) { // First node?
    list->tail = list->head;
  }
  list->length++;
  return node->data;
}

// Adds a node to end of list
void * list_append(List * list, const void * element) {
  ListNode * node = malloc(sizeof(ListNode));
  node->data = malloc(list->elementSize);
  memcpy(node->data, element, list->elementSize);
  node->next = NULL;
  // Place node at end of list
  if(list->length == 0)
    list->head = list->tail = node;
  else {
    list->tail->next = node;
    list->tail = node;
  }
  list->length++;
  return node->data;
}

// Size
int list_size(List * list) {
  return list->length;
}

// Head
ListNode * list_head(List * list) {
  return list->head;
}

// Tail
ListNode * list_tail(List * list) {
  return list->tail;
}

// Get the next element
ListNode * list_next(List * list, ListNode * current) {
  if(current == list->tail)
    return NULL;
  return current->next;
}

// list remove, returns an element from list (must be freed)
void * list_remove(List * list, void * element) {
  for(ListNode * ln = list->head, *prev = 0; ln; ln = ln->next) {
    if(memcmp(element, ln->data, list->elementSize) == 0) {
      // fix up nodes
      if(prev) // has previous node
        prev->next = ln->next;
      else // head of list
        list->head = ln->next;
      if(!ln->next) // end of list
        list->tail = prev;
      // retrieve the element
      void * ret = malloc(list->elementSize);
      memcpy(ret, ln->data, list->elementSize);
      if(list->freeFunc)
        list->freeFunc(ln->data);
      else
        free(ln->data);
      free(ln); // frees node
      list->length--;
      return ret;
    }
    prev = ln;
  }
  return NULL;
}

// deletes a node from the list - Warning for multiple deletes:
// possible for problems to occur if using a loop and freeing the
// underlying node mid-loop - to counter this, pass by reference
// sets the node at the next available, accordingly, this might skip nodes
// unless used carefully. Prefer using list_pop()
// if you insist on deleting multiple in a loop using this, don't increment
// unless it fails, and check for null after deleting
void list_delete_node(List * list, ListNode ** node, ListNode ** prev) { // careful with this
  if(list->length < 1) // Can't remove from empty list!
    return;
    ListNode * freenode = *node;
    *node = freenode->next; // set it to the next - whatever that may be
  // If the node is the head, no previous
  if(freenode == list->head) {
    if(list->length == 1) { // empty
         list->head = NULL;
         list->tail = NULL;
   } else {
         list->head = freenode->next;
   }
  } else {
    if(freenode == list->tail) {
      list->tail = (*prev);
    }
    (*prev)->next = *node;
  }
  // free node
  if(list->freeFunc) {
    list->freeFunc(freenode->data);
  } else
    free(freenode->data);
  free(freenode);
  list->length--;
}

// list delete element
// see remarks above about deleting nodes mid-loop
int list_delete(List * list, void * element) {
  for(ListNode *ln = list->head, *prev; ln; ln = ln->next) {
    if(memcmp(ln->data, element, list->elementSize) == 0) { // equal?
      list_delete_node(list, &ln, &prev);
      return 1;
    }
    prev = ln;
  }
  return 0;
}

ListNode * list_find(List * list, void * element) {
  for(ListNode * n = list->head; n; n = n->next) {
    if(memcmp(n->data, element, list->elementSize)) {
      return n;
    }
  }
  return NULL;
}

// Push
void * list_push(List * list, const void * element) {
  return list_append(list, element);
}

// indexes into list
void * list_index(List * list, int index, ListNode ** node, ListNode ** prev) {
  if(list->length <= 0) {

    return NULL;
  }
  if(index < 0) {
    index += list->length;
  }

  *node = list->head;
  for(int i = 0; i < index; i++) {
    *prev = *node;
    *node = (*node)->next;
    if(!*node) {

      return NULL;
    }
  }
  return (*node)->data;
}

// Pop
void * list_pop(List * list, int index) {
  ListNode *ln, *prev;
  void * data = list_index(list, index, &ln, &prev);
  if(data) {
    if(index == 0) { // at head?
      if(!(list->head = ln->next)) { // Null?
        list->tail = NULL;
      }
    } else if(ln == list->tail) { // at tail?
      list->tail = prev;
      prev->next = NULL;
    } else { // middle
      prev->next = ln->next;
    }
    free(ln);
    list->length--;
  }
  return data;
}

// Get
void * list_get(List * list, int index) {
  ListNode * ln, *prev;
  return list_index(list, index, &ln, &prev);
}

// Set
void * list_set(List * list, int index, void * value) {
  ListNode * ln, *prev;
  void * data = list_index(list, index, &ln, &prev); // index in
  if(data != NULL) {
    // take care of freeing node data
    if(list->freeFunc)
      list->freeFunc(data);
    else
      free(data);
    ln->data = malloc(list->elementSize);
    memcpy(ln->data, value, list->elementSize); // copy new value into data
  }
  return data;
}
