/*******************************************************************
*   Robert Nelson
*     string things on heap
********************************************************************/
// copy string onto heap
char * cstr_cpyh(const char * s);

// updates a string that was allocated
char * cstr_update(const char * newStr, char * buffer);

// retrieves substring starting at <start> of length <len>
//  if start is negative indexes from the end of the string
//  if the length exceeds string or is negative it copies till end
char * cstr_slice(const char * str, int start, int len);

// appends a string onto the current, original must be dynamic mem
// Does not free anything
char * cstr_join(const char * original, const char * new);

// joins an array of strings
char * cstr_join_arr(const char ** arr, int size, const char * delimiter);

// same as above, except updating original if possible
char * cstr_append(char * original, const char * new, int * originalLength);

// Appends a cstring to an original string and frees both the original
// and new memory
char * cstr_append_free(char * original, char * new);

// string append at - used for more rapid string appending
// if the string is longer than the maxMem, it allocates to double the size
// In order to properly track memory, maxMem MUST BE PASSED BY REFERENCE
// returns the pointer to the original
// useful for multiple insertions - does not null terminate
char * cstr_append_at(char ** original, const char * new, int * insert, int * maxMem);

// same as str_append_at except for single characters
char * cstr_append_char_at(char ** original, const char new, int * insert, int * maxMem);

// string equal
int cstr_eq(const char * str1, const char * str2);

// string equal ignoring case
int cstr_eq_ignore_case(const char * str1, const char * str2);

// string replace - replaces needle in haystack with replacement, count number of times
//    use a negative count to start at the end
// returns: allocated char * that must be freed
char * cstr_replace(const char * haystack, const char * needle, const char * replacement, int count);

// cstr_reverse
char * cstr_reverse(char * str);

// int to string
char * int_to_string(int num);

// string upper
char * cstr_upper(const char * s1);

int cstr_in(const char * haystack, const char * needle, int start);
