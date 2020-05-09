/*********************************************************************
*  String library
**********************************************************************/
#include <string.h>
#include <stdio.h>
#include <ctype.h>
#include <stdlib.h>
#include <unistd.h>
#include <stdbool.h>
#include "str.h"
#include "vector.h"

char STR_BUFFERIN[256];

// constructor
String * str(char * s) {
   if(!s || !*s)
      return 0;
   String * ret = malloc(sizeof(String));
   ret->capacity = ret->len = strlen(s);
   ret->str = malloc((ret->len + 1) * sizeof(char));
   ret->str[ret->len] = 0;
   strncpy(ret->str, s, ret->len);
   return ret;
}

// same as above but with size determined
String * str_(char * s, int size) {
   String * ret = malloc(sizeof(String));
   ret->capacity = ret->len = size;
   ret->str = malloc((size + 1) * sizeof(char));
   ret->str[ret->len] = 0;
   memcpy(ret->str, s, size);
   return ret;
}


// for creating a string to be filled
String * str_empty(int capacity) {
   String * ret = malloc(sizeof(String));
   ret->capacity = capacity;
   ret->str = malloc((capacity + 1) * sizeof(char));
   ret->str[0] = 0;
   return ret;
}

// destructor
void str_free(String * str) {
   if(str) {
      free(str->str);
      free(str);
   }
}

// destructor taking a pointer to the pointed string
void str_freepointer(String ** str) {
   str_free(*str);
}

// copy
String * str_copy(const String * str) {
   String * ret = malloc(sizeof(String));
   ret->capacity = ret->len = str->len;
   ret->str = malloc((ret->len + 1) * sizeof(char));
   ret->str[ret->len] = 0;
   memcpy(ret->str, str->str, ret->len);
   return ret;
}

// Join
String * str_join(const String * str1, const String * str2) {
   String * s = malloc(sizeof(String));
   s->capacity = s->len = str1->len + str2->len;
   s->str = malloc((s->len + 1) * sizeof(char));
   s->str[s->len] = 0;
   memcpy(s->str, str1, str1->len);
   memcpy(s->str + str1->len, str2, str2->len);
   return s;
}

// Add
void str_add(String * str1, const String * str2) {
   str_append(str1, str2->str, str2->len);
}

// append
void str_append(String * str, const char * cptr, int length) {
   int newlen = str->len + length;
   if(newlen > str->capacity) {
      str_resize(str, newlen);
   }
   memcpy(str->str + str->len, cptr, length);
   str->str[newlen] = 0;
   str->len = newlen;
}

// slice from [start:end)
String * str_slice(const String * str1, int start, int end) {
   if(end <= STR_END)
      end = str1->len + 1;
   if(end < start || end > str1->len + 1) // nope
      return NULL;
   else if(end == start)
      end += 1;
   String * s = malloc(sizeof(String));
   s->capacity = s->len = end - start;
   s->str = malloc((s->len + 1) * sizeof(char));
   s->str[s->len] = 0;
   memcpy(s->str, str1->str + start, s->len);
   return s;
}

// Replace
String * str_replace(const String * haystack, const String * needle, const String * replacement, int count) {
   int stopat = haystack->len - needle->len, replacementCount = 0;
   char *s1 = haystack->str, *s2 = needle->str;
   if(!count)
      count = haystack->len / needle->len;
   int replaceIndices[count];
   for(int i = 0; i <= stopat; i++) {
      // check first char
      if(s1[i] == *s2) {
         if(memcmp(s1 + i, s2, needle->len) == 0) {
            replaceIndices[replacementCount] = i;
            if(++replacementCount >= count)
               break;
         }
      }
   }
   int replaceLen = (replacement ? replacement->len : 0), replacePoint, start = 0;
   int newlen = (replaceLen - needle->len) * replacementCount + haystack->len;
   String * new = str_empty(newlen);
   char *newcstr = new->str;
   newcstr[newlen] = 0;
   // now construct the new string
   for(int i = 0; i < replacementCount; i++) {
      replacePoint = replaceIndices[i]; // replacement point in haystack
      // copy haystack
      memcpy(newcstr, s1 + start, replacePoint - start);
      newcstr += replacePoint;
      // copy replacement
      memcpy(newcstr, replacement, replaceLen);
      newcstr += replaceLen;
      start = replacePoint + needle->len;
   }
   // copy rest of haystack
   memcpy(newcstr, s1 + start, haystack->len - start);
   new->len = newlen;
   return new;
}

// is string in - returns -1 if not found
int str_in(const String * haystack, const String * needle, int start) {
   if(start >= haystack->len)
      return STR_NOT_FOUND;
   char *h = haystack->str, *n = needle->str;
   for(int i = start, nlen = needle->len, maxI = haystack->len - nlen; i <= maxI; i++) {
      if(h[i] == *n && (memcmp(h + i, n, nlen) == 0)) {
         return i;
      }
   }
   return STR_NOT_FOUND;
}

// is string in - returns -1 if not found
int str_in_ignore_case(const String * haystack, const String * needle, int start) {
   if(start >= haystack->len)
      return STR_NOT_FOUND;
   char *h = haystack->str, *n = needle->str;
   for(int i = start, nlen = needle->len, maxI = haystack->len - nlen; i <= maxI; i++) {
      if(toupper(h[i]) == toupper(*n)) {
         for(char *hay = h + i + 1, *ne = n + 1; toupper(*h) == toupper(*ne); h++, ne++) {
            if(!*ne)
               return i;
            else if(!*hay)
               return STR_NOT_FOUND;
         }
      }
   }
   return STR_NOT_FOUND;
}

// is string in - returns -1 if not found
int strc_in_ignore_case(const String * haystack, const char * needle, int start) {
   if(start >= haystack->len)
      return STR_NOT_FOUND;
   char *h = haystack->str, *n = needle;
   for(int i = start, nlen = strlen(needle), maxI = haystack->len - nlen; i <= maxI; i++) {
      if(toupper(h[i]) == toupper(*n)) {
         for(char * hay = h + i + 1, *ne = n + 1; toupper(*h) == toupper(*ne); h++, ne++) {
            if(!*ne)
               return i;
            else if(!*hay)
               return STR_NOT_FOUND;
         }
      }
   }
   return STR_NOT_FOUND;
}


// upper
void str_upper(String * string) {
   char *c = string->str;
   for(int i = 0; i < string->len; i++) {
      c[i] = toupper(c[i]);
   }
}

// lower
void str_lower(String * string) {
   char *c = string->str;
   for(int i = 0; i < string->len; i++) {
      c[i] = tolower(c[i]);
   }
}

// print
void str_print(String * string) {
   fwrite(string->str, 1, string->len, stdout);
}

// print n
void str_printn(String * string, int n) {
   if(n > string->len)
      n = string->len;
   fwrite(string->str, 1, n, stdout);
}

// stdin get
String * str_get() {
   int start = 0;
   String *s = str_empty(64);
   while(fgets(s->str + start, s->capacity, stdin)) {
      start += strlen(s->str);
      // did it get new line?
      if(s->str[start - 1] == '\n') {
         s->str[(s->len = start - 1)] = 0;
         break;
      }
      str_resize(s, s->capacity * 2);
   }
   return s;
}


// err
void str_err(String * string) {
   fwrite(string->str, 1, string->len, stderr);
}

// write
int str_write(String * str, int fd) {
   write(fd, str->str, str->len);
}

// read
String * str_read(int fd, int amount) {
   String * str = str_empty(amount);
   if((str->len = read(fd, str->str, amount)) <= 0) {
      str_free(str);
      return NULL;
   }
   str->str[str->len] = 0;
   return str;
}


// trim a string
int str_trim(String * str, const char * chrs) {
   if(!chrs || !*chrs) {
      chrs = " \f\r\n\t\v";
   }
   int startTrim = 0, endTrim = 0;
   bool running;
   char * tmp, *trim;
   // from the start
   for(int i = 0; i < str->len; i++) {
      running = false;
      for(trim = chrs; *trim; trim++) {
         if(*trim == tmp[i]) {
            ++startTrim;
            running = true;
            break;
         }
      }
      if(!running)
         break;
   }
   // from the end
   for(int i = str->len - 1; i >= startTrim; i--) {
      running = false;
      for(trim = chrs; *trim; trim++) {
         if(*trim == tmp[i]) {
            ++endTrim;
            running = true;
            break;
         }
      }
      if(!running)
         break;
   }
   if(!endTrim && !startTrim)
      return 0;
   tmp = str->str;
   if((str->len -= endTrim + startTrim) < 0) {
      str->len = 0;
   } else
      // shift string if applicable
      for(int i = startTrim, j = 0; j < str->len; i++, j++) {
         tmp[j] = tmp[i];
      }
   str->str[str->len] = 0;
   return endTrim + startTrim;
}

bool str_eq(const String * s1, const String * s2) {
   if(s1->len != s2->len)
      return false;
   return memcmp(s1->str, s2->str, s1->len) == 0;
}

bool str_eq_ignore_case(const String * s1, const String * s2) {
   if(s1->len != s2->len)
      return false;
   for(char * c1 = s1->str, *c2 = s2->str; *c1; c1++, c2++) {
      if(*c1 != *c2)
         return false;
   }
   return true;
}

Vector * str_split(const String * haystack, const String * needle) {
   int start = 0, end = 0;
   if((end = str_in(haystack, needle, 0)) == STR_NOT_FOUND) {
      return NULL;
   }
   Vector * ret = vector_new(8, sizeof(String *), str_freepointer);
   String * sub = str_slice(haystack, start, end);
   vector_push(ret, &sub);
   start = end + needle->len;
   while((end = str_in(haystack, needle, start)) != STR_NOT_FOUND) {
      sub = str_slice(haystack, start, end);
      vector_push(ret, &sub);
      start = end + needle->len;
   }
   if(start < haystack->len) {
      sub = str_slice(haystack, start, haystack->len);
      vector_push(ret, &sub);
   }

   return ret;
}

bool strc_eq(const String * s1, const char * s2) {
   return strcmp(s1->str, s2) == 0;
}

bool strc_eq_ignore_case(const String * s1, const char * s2) {
   if(s1 == NULL || s2 == NULL)
      printf("STRING IS NULL!\n");
   const char *c1 = s1->str, *c2 = s2;
   for(; *c1 && *c2; c1++, c2++)
      if(toupper(*c1) != toupper(*c2))
         return false;
   return !(*c1 || *c2);
}

String * strc_replace(const String * haystack, const char * needle, const char * replacement, int count) {
   String *n = str(needle), *rep = str(replacement);
   String * result = str_replace(haystack, n, rep, count);
   str_free(n);
   str_free(rep);
   return result;
}

int strc_in(const String * haystack, const char * needle, int start) {
   char * res = strstr(haystack->str + start, needle);
   return res ? res - haystack->str : STR_NOT_FOUND;
}

Vector * strc_split(const String * haystack, const char * needle) {
   int start = 0, end = 0, nlen = strlen(needle);
   if((end = strc_in(haystack, needle, 0)) == STR_NOT_FOUND)
      return NULL;
   Vector * ret = vector_new(8, sizeof(String *), (FreeFunc) str_freepointer);
   String * sub = str_slice(haystack, start, end);
   vector_push(ret, &sub);
   start = end + nlen;
   while((end = strc_in(haystack, needle, start)) != STR_NOT_FOUND) {
      sub = str_slice(haystack, start, end);
      vector_push(ret, &sub);
      start = end + nlen;
   }
   if(start < haystack->len) {
      sub = str_slice(haystack, start, haystack->len);
      vector_push(ret, &sub);
   }
   return ret;
}

// resize.. capacity must be greater than current
void str_resize(String * s, int capacity) {
   char * ptr = realloc(s->str, capacity + 1);
   if(!ptr) {
      ptr = malloc((capacity + 1) * sizeof(char));
      memcpy(ptr, s->str, s->len);
      free(s->str);
   }
   s->str = ptr;
   s->capacity = capacity;
}
