#ifndef EGA_VERTHASH_H
#define EGA_VERTHASH_H

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

void verthash_hash(const unsigned char* blob_bytes, const size_t blob_size,
                   const unsigned char* input, const size_t input_size,
                   unsigned char* output);

#ifdef __cplusplus
}
#endif

#endif
