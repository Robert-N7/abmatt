/*******************************************************************
*   Robert Nelson
*     string things on heap
********************************************************************/
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include "stringUtil.h"

// copy string onto heap
char * cstr_cpyh(const char * s) {
  if(!s)
    return 0;
  char * news = malloc(strlen(s) + 1);
  strcpy(news, s);
  return news;
}

// updates a string that was allocated
char * cstr_update(const char * newStr, char * buffer) {
    int size = strlen(newStr);
    if(buffer == NULL || strlen(buffer) < size) {
        free(buffer);
        buffer = malloc(size + 1);
    }
    strcpy(buffer, newStr);
    return buffer;
}

// retrieves substring starting at <start> of length <len>
//  if start is negative indexes from the end of the string
//  if the length exceeds string or is negative it copies till end
char * cstr_slice(const char * str, int start, int len) {
    int clen = strlen(str);
    if(start < 0)
      start += clen;
   if(len <= 0)
      len += clen - start;

    if(start + len > clen)
      len = clen - start;
    char * r = malloc(len + 1);
    strncpy(r, str + start, len);
    r[len] = 0;
    return r;
}

// joins an array of strings
char * cstr_join_arr(const char ** arr, int size, const char * delimiter) {
  int len = 0;
  int delLen = strlen(delimiter);
  // first run to get size
  for(int i = 0; i < size; i++) {
    len += strlen(arr[i]);
  }
  char * ptr = malloc(delLen * (size - 1) + len + 1);
  char * c = ptr;
  for(int i = 0; i < size; i++) { // each string
    for(const char * copy = arr[i]; *copy; copy++) { // each char
      *c = *copy;
      ++c;
    }
    if(delLen && i != size - 1) {
      strncpy(c, delimiter, delLen);
      c += delLen;
    }
  }
  ptr[len] = 0;
  return ptr;
}

// appends a string onto the current
char * cstr_join(const char * original, const char * new) {
  if(!new)
    return cstr_cpyh(original);
  else if(!original)
    return cstr_cpyh(new);
  int new_size = strlen(new);
  int original_size = strlen(original);
  char * ptr = malloc(original_size + new_size + 1);
  if(new) { // not null?
    strncpy(ptr, original, original_size);
    strcpy(ptr + original_size, new);
  } else {
    strcpy(ptr, original);
  }
  return ptr;
}

// same as above, except updating original if possible
char * cstr_append(char * original, const char * new, int * originalLength) {
  if(!new)
    return NULL;
  int new_size = strlen(new), original_size;
  if(!originalLength)
    original_size = strlen(original);
  else
    original_size = *originalLength;
  char * ptr = realloc(original, new_size + original_size + 1);
  if(!ptr) {
    ptr = malloc(original_size + new_size + 1);
    strncpy(ptr, original, original_size);
    free(original);
  }
  strcpy(ptr + original_size, new);
  *originalLength = original_size + new_size;
  return ptr;
}

// same as above, except freeing the new string
char * cstr_append_free(char * original, char * new) {
  int new_size = strlen(new);
  int original_size = strlen(original);
  char * ptr = malloc(original_size + new_size + 1);
  strncpy(ptr, original, original_size);
  strcpy(ptr + original_size, new);
  free(original);
  free(new);
  return ptr;
}


// string append at - used for more rapid string appending
// if the string is longer than the maxMem, it allocates to double the size
// In order to properly track memory maxMem MUST BE PASSED BY REFERENCE
// Additionally original MUST BE PASSED BY REFERENCE
// returns the new insertion point
// useful for multiple insertions - does not null terminate
char * cstr_append_at(char ** original, const char * new, int * insert, int * maxMem) {
  if(!new) // check for null
    return *original;
  if(*maxMem <= 0) {
    *maxMem += 16;
    *original = malloc(*maxMem);
  }

  for(const char * c = new; *c; c++, (*insert)++) {
    if(*insert >= *maxMem - 2) {
      *maxMem *= 2;
      char * ptr = realloc(*original, *maxMem);
      if(ptr == NULL) { // Failed to reallocate
        ptr = malloc(*maxMem);
        strncpy(ptr, *original, *insert - 1);
      }
      *original = ptr;
    }
    (*original)[*insert] = *c;
  }

  return *original;
}

// same as str_append_at except for single characters
char * cstr_append_char_at(char ** original, char new, int * insert, int * maxMem) {
  if(*insert >= *maxMem - 2) {
    *maxMem *= 2;
    char * ptr = realloc(*original, *maxMem);
    if(ptr == NULL) { // Failed to reallocate
      ptr = malloc(*maxMem);
      strncpy(ptr, *original, *insert - 1);
    }
    *original = ptr;
  }
  (*original)[*insert] = new;
  (*insert)++;
  return *original;
}

int cstr_eq(const char * str1, const char * str2) {
  if(!str1 || !str2) // null case
    return str1 == str2;
  return strcmp(str1, str2) == 0;
}

int cstr_eq_ignore_case(const char * str1, const char * str2) {
  for (; *str1 && *str2; str1++, str2++) {
    if(toupper(*str1) != toupper(*str2))
      return 0;
  }
  return *str1 == *str2; // must be 0 == 0
}

// string replace - replaces needle in haystack with replacement, count number of times
//    use a negative count to start at the end
// returns: allocated char * that must be freed
char * cstr_replace(const char * haystack, const char * needle, const char * replacement, int count) {
    int needleLen = strlen(needle), reverse = 0, replacementLen = 0;
    if(replacement)
      replacementLen = strlen(replacement);

    char * li[strlen(haystack) / needleLen];
    // first pass to determine occurrence
    const char *c;
    int max = 0;
    for(c = haystack; *c; c++) {
      if(*c == *needle && memcmp(c, needle, needleLen) == 0) { // found one
        li[max++] = c;
        c += needleLen - 1;
      }
    }
    if(count < 0) {
      reverse = 1;
      count *= -1;
    // can't replace more than the max occurrence
    } else if (count == 0 || count > max) {
      count = max;
    }
    int i = 0, cpylen = 0, haylen = c-haystack;
    int newlength = (replacementLen - needleLen) * count + haylen;
    // Now allocate and create the new string

    char * newstr = malloc(newlength + 1);
    char * c2 = newstr;
    c = haystack;
    c2 = newstr;
    int liIt = 0;
    if(reverse) { // remove extra occurrences
      while(max - liIt > count)
        ++liIt;
    }

    for(; liIt < max; liIt++) {
      cpylen = li[liIt] - c; // how much to copy

      memcpy(c2, c, cpylen);
      c2 += cpylen; // advance strings
      memcpy(c2, replacement, replacementLen);

      c2 += replacementLen; // advance strings
      c += needleLen + cpylen;
      if(++i >= count) // limit occurrence and we've reached the limit
        break;
    }
    // copy the rest
    if(cpylen= haystack + haylen - c) {
      memcpy(c2, c, cpylen);
      c2 += cpylen;
    }
    c2[0] = '\0'; // null terminate
    return newstr;
}

// str reverse
char * cstr_reverse(char * str) {
  int length = strlen(str);
  char * newstr = malloc(length + 1);
  for(char *c1 = str, *c2 = newstr + length; *c1; c1++) {
    *c2 = *c1;
    --c2;
  }
  newstr[length] = 0;
  return newstr;
}

// int_to_string()
char * int_to_string(int num) {
	int i = 0, isNegative = 0, numDigits = 0;
	/* Handle 0 explicitely, otherwise empty string is printed for 0 */
	if (num == 0) {
    char * str = malloc(2);
    str[i] = '0';
		str[++i] = '\0';
		return str;
	}
  for(int j = num; j != 0; j /= 10)
    ++numDigits;
	if (num < 0) {
		isNegative = 1;
		num *= -1;
    ++numDigits;
	}
  char * newstr = malloc(numDigits + 1);
  newstr[numDigits] = 0; // null terminate
	// Process individual digits
	for(i = numDigits; num > 0; num /= 10)
		newstr[--i] = num % 10 + '0';
	if (isNegative)
		newstr[--i] = '-';
	return newstr;
}

// string upper
char * cstr_upper(const char * s1) {
    char * ret = malloc(strlen(s1) + 1);
    char * c2 = ret;
    for(char *c1 = s1; *c1; c1++) {
      *c2 = toupper(*c1);
      ++c2;
    }
    *c2 = 0;
    return ret;
}

// str_equal_ignore_case
int cstr_equal_ignore_case(const char * string1, const char * string2) {
  char *s1, *s2;
  for(s1 = string1, s2 = string2; s1 && s2; s1++, s2++) {
    if(toupper(s1) != toupper(s2))
      return 0;
  }
  return !(s1 || s2); // either not null?
}

// is str in haystack? returns -1 if not found, otherwise returns index
int cstr_in(const char * haystack, const char * needle, int start) {
  int needleLen = strlen(needle), i = 0;
  if(start < 0)
    start += strlen(haystack);
  for(char *c1 = haystack + start, *c2 = needle; *c1; c1++, i++) {
    if(*c1 == *c2 && memcmp(c1, c2, needleLen) == 0) {
      return start + i;
    }
  }
  return -1;
}
