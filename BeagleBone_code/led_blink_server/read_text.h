#ifndef READ_TEXT_H
#define READ_TEXT_H

#include <stdint.h>


void skip_whitespace(const char **ptr,char skip_cr);
char to_nextline(const char **ptr);
char read_identifier(const char **ptr,char *buffer,unsigned int buffersize);
char read_int(const char **ptr,int32_t *result);
char read_uint(const char **ptr,uint32_t *result);
char read_int64(const char **ptr,int64_t *result);
char read_double(const char **ptr,double *result);
char read_bool(const char **ptr,char *result);
char read_vector(const char **ptr,unsigned int components,double *result_array);







#endif
