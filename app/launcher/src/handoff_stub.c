/* app/launcher/src/handoff_stub.c — SOCCER 13 Direct Boot & Interactive Graphics Selector
 * Model 1: Displays vertical graphics preset selector at boot using assets/bg.jpg,
 * applies selected settings.dat, cleanly releases VideoOut/Pad, and transfers
 * execution to relocated_wine_app.prx in game mode.
 *
 * Implements strict no-RELRO layout, uses ONLY libkernel.so direct imports,
 * and dynamically resolves VideoOut/Pad to guarantee ZERO CE-34878-0 crashes.
 */

#include <orbis/libkernel.h>
#include <orbis/VideoOut.h>
#include <orbis/Pad.h>
#include <orbis/UserService.h>
#include <orbis/_types/pad.h>

#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

enum { MODULE_INFO_BYTES = 0x160, MAX_SEGMENTS = 4, MAX_EXPORTS = 8 };
#define PRX_MAGIC UINT64_C(0x3143534544585250)
typedef struct { const char *name; const void *address; } Export;
typedef struct { uint64_t magic; uint32_t version, count; Export exports[]; } Descriptor;
typedef struct { const void *address; uint32_t size, protection; } Segment;
typedef void (*Entry)(int, char **);

#define SCREEN_WIDTH  1920
#define SCREEN_HEIGHT 1080
#define FRAME_BYTES   (SCREEN_WIDTH * SCREEN_HEIGHT * 4)
#define NUM_BUFFERS   2
#define TOTAL_VMEM    (FRAME_BYTES * NUM_BUFFERS)
#define DIRECT_ALIGN  0x200000
#define DIRECT_TYPE   3 /* ORBIS_KERNEL_WC_GARLIC */
#define PIXEL_FORMAT  0x80000000 /* PIXEL_A8R8G8B8_SRGB */

/* Dynamic Function Pointer Types for Userland Modules */
typedef int32_t (*Pfn_sceVideoOutOpen)(int32_t userId, int32_t type, int32_t index, const void *param);
typedef int32_t (*Pfn_sceVideoOutClose)(int32_t handle);
typedef int32_t (*Pfn_sceVideoOutSetFlipRate)(int32_t handle, int32_t rate);
typedef int32_t (*Pfn_sceVideoOutSetBufferAttribute)(OrbisVideoOutBufferAttribute *attr, uint32_t pixelFormat, uint32_t tilingMode, uint32_t aspectRatio, uint32_t width, uint32_t height, uint32_t pitch);
typedef int32_t (*Pfn_sceVideoOutRegisterBuffers)(int32_t handle, int32_t startIndex, void * const *addresses, int32_t bufferNum, const OrbisVideoOutBufferAttribute *attr);
typedef int32_t (*Pfn_sceVideoOutUnregisterBuffers)(int32_t handle, int32_t startIndex);
typedef int32_t (*Pfn_sceVideoOutSubmitFlip)(int32_t handle, int32_t bufferIndex, int32_t flipMode, int64_t arg);

typedef int32_t (*Pfn_scePadInit)(void);
typedef int32_t (*Pfn_scePadOpen)(int32_t userId, int32_t type, int32_t index, const void *param);
typedef int32_t (*Pfn_scePadRead)(int32_t handle, OrbisPadData *data, int32_t count);
typedef int32_t (*Pfn_scePadClose)(int32_t handle);

typedef int32_t (*Pfn_sceUserServiceInitialize)(const void *param);
typedef int32_t (*Pfn_sceUserServiceGetInitialUser)(int32_t *userId);

static Pfn_sceVideoOutOpen fn_sceVideoOutOpen = NULL;
static Pfn_sceVideoOutClose fn_sceVideoOutClose = NULL;
static Pfn_sceVideoOutSetFlipRate fn_sceVideoOutSetFlipRate = NULL;
static Pfn_sceVideoOutSetBufferAttribute fn_sceVideoOutSetBufferAttribute = NULL;
static Pfn_sceVideoOutRegisterBuffers fn_sceVideoOutRegisterBuffers = NULL;
static Pfn_sceVideoOutUnregisterBuffers fn_sceVideoOutUnregisterBuffers = NULL;
static Pfn_sceVideoOutSubmitFlip fn_sceVideoOutSubmitFlip = NULL;

static Pfn_scePadInit fn_scePadInit = NULL;
static Pfn_scePadOpen fn_scePadOpen = NULL;
static Pfn_scePadRead fn_scePadRead = NULL;
static Pfn_scePadClose fn_scePadClose = NULL;

static Pfn_sceUserServiceInitialize fn_sceUserServiceInitialize = NULL;
static Pfn_sceUserServiceGetInitialUser fn_sceUserServiceGetInitialUser = NULL;

static uint32_t s_mod_video = 0;
static uint32_t s_mod_pad = 0;
static uint32_t s_mod_user = 0;

static const char *const libkernel_symbols[] __attribute__((unused)) = {
#include "libkernel-symbols.inc"
};

/* 8x16 Bitmap Font */
static const uint8_t s_font[96][16] = {
    {0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00}, // 32 ' '
    {0x00,0x00,0x18,0x3C,0x3C,0x3C,0x18,0x18,0x18,0x00,0x18,0x18,0x00,0x00,0x00,0x00}, // 33 '!'
    {0x00,0x66,0x66,0x66,0x24,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00}, // 34 '"'
    {0x00,0x00,0x6C,0x6C,0xFE,0x6C,0x6C,0x6C,0xFE,0x6C,0x6C,0x00,0x00,0x00,0x00,0x00}, // 35 '#'
    {0x18,0x18,0x7C,0xC6,0xC2,0xC0,0x7C,0x06,0x06,0x86,0xC6,0x7C,0x18,0x18,0x00,0x00}, // 36 '$'
    {0x00,0x00,0x00,0x00,0xC2,0xC6,0x0C,0x18,0x30,0x60,0xC6,0x86,0x00,0x00,0x00,0x00}, // 37 '%'
    {0x00,0x00,0x38,0x6C,0x6C,0x38,0x76,0xDC,0xCC,0xCC,0xCC,0x76,0x00,0x00,0x00,0x00}, // 38 '&'
    {0x00,0x30,0x30,0x18,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00}, // 39 '''
    {0x00,0x0C,0x18,0x30,0x30,0x60,0x60,0x60,0x60,0x60,0x30,0x30,0x18,0x0C,0x00,0x00}, // 40 '('
    {0x00,0x30,0x18,0x0C,0x0C,0x06,0x06,0x06,0x06,0x06,0x0C,0x0C,0x18,0x30,0x00,0x00}, // 41 ')'
    {0x00,0x00,0x00,0x66,0x3C,0xFF,0x3C,0x66,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00}, // 42 '*'
    {0x00,0x00,0x00,0x18,0x18,0x7E,0x18,0x18,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00}, // 43 '+'
    {0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x18,0x18,0x18,0x08,0x10,0x00,0x00}, // 44 ','
    {0x00,0x00,0x00,0x00,0x00,0x7E,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00}, // 45 '-'
    {0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x18,0x18,0x00,0x00,0x00,0x00}, // 46 '.'
    {0x00,0x00,0x02,0x06,0x0C,0x18,0x30,0x60,0xC0,0x80,0x00,0x00,0x00,0x00,0x00,0x00}, // 47 '/'
    {0x00,0x00,0x3C,0x66,0xC3,0xE3,0xD3,0xCB,0xC7,0xC3,0x66,0x3C,0x00,0x00,0x00,0x00}, // 48 '0'
    {0x00,0x00,0x18,0x78,0x18,0x18,0x18,0x18,0x18,0x18,0x18,0x7E,0x00,0x00,0x00,0x00}, // 49 '1'
    {0x00,0x00,0x7C,0xC6,0x06,0x0C,0x18,0x30,0x60,0xC0,0xC6,0xFE,0x00,0x00,0x00,0x00}, // 50 '2'
    {0x00,0x00,0x7C,0xC6,0x06,0x06,0x3C,0x06,0x06,0x06,0xC6,0x7C,0x00,0x00,0x00,0x00}, // 51 '3'
    {0x00,0x00,0x0C,0x1C,0x3C,0x6C,0xCC,0xFE,0x0C,0x0C,0x0C,0x1E,0x00,0x00,0x00,0x00}, // 52 '4'
    {0x00,0x00,0xFE,0xC0,0xC0,0xFC,0x06,0x06,0x06,0x06,0xC6,0x7C,0x00,0x00,0x00,0x00}, // 53 '5'
    {0x00,0x00,0x38,0x60,0xC0,0xC0,0xFC,0xC6,0xC6,0xC6,0xC6,0x7C,0x00,0x00,0x00,0x00}, // 54 '6'
    {0x00,0x00,0xFE,0xC6,0x06,0x0C,0x18,0x30,0x30,0x60,0x60,0x60,0x00,0x00,0x00,0x00}, // 55 '7'
    {0x00,0x00,0x7C,0xC6,0xC6,0xC6,0x7C,0xC6,0xC6,0xC6,0xC6,0x7C,0x00,0x00,0x00,0x00}, // 56 '8'
    {0x00,0x00,0x7C,0xC6,0xC6,0xC6,0x7E,0x06,0x06,0x06,0x0C,0x78,0x00,0x00,0x00,0x00}, // 57 '9'
    {0x00,0x00,0x00,0x18,0x18,0x00,0x00,0x00,0x00,0x18,0x18,0x00,0x00,0x00,0x00,0x00}, // 58 ':'
    {0x00,0x00,0x00,0x18,0x18,0x00,0x00,0x00,0x00,0x18,0x18,0x08,0x10,0x00,0x00,0x00}, // 59 ';'
    {0x00,0x06,0x0C,0x18,0x30,0x60,0xC0,0x60,0x30,0x18,0x0C,0x06,0x00,0x00,0x00,0x00}, // 60 '<'
    {0x00,0x00,0x00,0x00,0x7E,0x00,0x00,0x7E,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00}, // 61 '='
    {0x00,0x60,0x30,0x18,0x0C,0x06,0x03,0x06,0x0C,0x18,0x30,0x60,0x00,0x00,0x00,0x00}, // 62 '>'
    {0x00,0x00,0x7C,0xC6,0x06,0x0C,0x18,0x18,0x00,0x18,0x18,0x00,0x00,0x00,0x00,0x00}, // 63 '?'
    {0x00,0x00,0x7C,0xC6,0xC6,0xDE,0xDE,0xDE,0xDC,0xC0,0x7C,0x00,0x00,0x00,0x00,0x00}, // 64 '@'
    {0x00,0x00,0x18,0x3C,0x66,0xC3,0xC3,0xFF,0xC3,0xC3,0xC3,0xC3,0x00,0x00,0x00,0x00}, // 65 'A'
    {0x00,0x00,0xFC,0x66,0x66,0x7C,0x66,0x66,0x66,0x66,0x66,0xFC,0x00,0x00,0x00,0x00}, // 66 'B'
    {0x00,0x00,0x3C,0x66,0xC3,0xC0,0xC0,0xC0,0xC0,0xC3,0x66,0x3C,0x00,0x00,0x00,0x00}, // 67 'C'
    {0x00,0x00,0xF8,0x6C,0x66,0x66,0x66,0x66,0x66,0x66,0x6C,0xF8,0x00,0x00,0x00,0x00}, // 68 'D'
    {0x00,0x00,0xFE,0x62,0x62,0x68,0x78,0x68,0x60,0x62,0x62,0xFE,0x00,0x00,0x00,0x00}, // 69 'E'
    {0x00,0x00,0xFE,0x62,0x62,0x68,0x78,0x68,0x60,0x60,0x60,0xF0,0x00,0x00,0x00,0x00}, // 70 'F'
    {0x00,0x00,0x3C,0x66,0xC3,0xC0,0xC0,0xCF,0xC3,0xC3,0x66,0x3A,0x00,0x00,0x00,0x00}, // 71 'G'
    {0x00,0x00,0xC3,0xC3,0xC3,0xC3,0xFF,0xC3,0xC3,0xC3,0xC3,0xC3,0x00,0x00,0x00,0x00}, // 72 'H'
    {0x00,0x00,0x7E,0x18,0x18,0x18,0x18,0x18,0x18,0x18,0x18,0x7E,0x00,0x00,0x00,0x00}, // 73 'I'
    {0x00,0x00,0x1E,0x06,0x06,0x06,0x06,0x06,0x06,0xC6,0xC6,0x7C,0x00,0x00,0x00,0x00}, // 74 'J'
    {0x00,0x00,0xC3,0xC6,0xCC,0xD8,0xF0,0xD8,0xCC,0xC6,0xC3,0xC3,0x00,0x00,0x00,0x00}, // 75 'K'
    {0x00,0x00,0xF0,0x60,0x60,0x60,0x60,0x60,0x60,0x62,0x66,0xFE,0x00,0x00,0x00,0x00}, // 76 'L'
    {0x00,0x00,0xC3,0xE7,0xFF,0xDB,0xC3,0xC3,0xC3,0xC3,0xC3,0xC3,0x00,0x00,0x00,0x00}, // 77 'M'
    {0x00,0x00,0xC3,0xE3,0xF3,0xDB,0xCF,0xC7,0xC3,0xC3,0xC3,0xC3,0x00,0x00,0x00,0x00}, // 78 'N'
    {0x00,0x00,0x7C,0xC6,0xC6,0xC6,0xC6,0xC6,0xC6,0xC6,0xC6,0x7C,0x00,0x00,0x00,0x00}, // 79 'O'
    {0x00,0x00,0xFC,0x66,0x66,0x66,0x7C,0x60,0x60,0x60,0x60,0xF0,0x00,0x00,0x00,0x00}, // 80 'P'
    {0x00,0x00,0x7C,0xC6,0xC6,0xC6,0xC6,0xC6,0xC6,0xD6,0xDE,0x7C,0x0E,0x00,0x00,0x00}, // 81 'Q'
    {0x00,0x00,0xFC,0x66,0x66,0x66,0x7C,0x6C,0x66,0x66,0x66,0xE3,0x00,0x00,0x00,0x00}, // 82 'R'
    {0x00,0x00,0x7E,0xC3,0xC0,0xC0,0x7E,0x03,0x03,0x03,0xC3,0x7E,0x00,0x00,0x00,0x00}, // 83 'S'
    {0x00,0x00,0xFF,0x18,0x18,0x18,0x18,0x18,0x18,0x18,0x18,0x3C,0x00,0x00,0x00,0x00}, // 84 'T'
    {0x00,0x00,0xC3,0xC3,0xC3,0xC3,0xC3,0xC3,0xC3,0xC3,0xC3,0x7E,0x00,0x00,0x00,0x00}, // 85 'U'
    {0x00,0x00,0xC3,0xC3,0xC3,0xC3,0xC3,0xDB,0xFF,0xE7,0xC3,0xC3,0x00,0x00,0x00,0x00}, // 87 'W'
    {0x00,0x00,0xC3,0xC3,0x66,0x3C,0x18,0x3C,0x66,0xC3,0xC3,0xC3,0x00,0x00,0x00,0x00}, // 88 'X'
    {0x00,0x00,0xC3,0xC3,0xC3,0x66,0x3C,0x18,0x18,0x18,0x18,0x3C,0x00,0x00,0x00,0x00}, // 89 'Y'
    {0x00,0x00,0xFF,0xC3,0x86,0x0C,0x18,0x30,0x60,0xC1,0xC3,0xFF,0x00,0x00,0x00,0x00}, // 90 'Z'
    {0x00,0x3C,0x30,0x30,0x30,0x30,0x30,0x30,0x30,0x30,0x30,0x3C,0x00,0x00,0x00,0x00}, // 91 '['
    {0x00,0x3C,0x0C,0x0C,0x0C,0x0C,0x0C,0x0C,0x0C,0x0C,0x0C,0x3C,0x00,0x00,0x00,0x00}, // 93 ']'
    {0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xFF,0x00,0x00,0x00}, // 95 '_'
    {0x00,0x00,0x00,0x00,0x00,0x78,0x0C,0x7C,0xCC,0xCC,0xCC,0x76,0x00,0x00,0x00,0x00}, // 97 'a'
    {0x00,0x00,0xE0,0x60,0x60,0x7C,0x66,0x66,0x66,0x66,0x66,0xDC,0x00,0x00,0x00,0x00}, // 98 'b'
    {0x00,0x00,0x00,0x00,0x00,0x7C,0xC6,0xC0,0xC0,0xC0,0xC6,0x7C,0x00,0x00,0x00,0x00}, // 99 'c'
    {0x00,0x00,0x1C,0x0C,0x0C,0x7C,0xCC,0xCC,0xCC,0xCC,0xCC,0x76,0x00,0x00,0x00,0x00}, // 100 'd'
    {0x00,0x00,0x00,0x00,0x00,0x7C,0xC6,0xFE,0xC0,0xC0,0xC6,0x7C,0x00,0x00,0x00,0x00}, // 101 'e'
    {0x00,0x00,0x38,0x6C,0x64,0x60,0xF0,0x60,0x60,0x60,0x60,0xF0,0x00,0x00,0x00,0x00}, // 102 'f'
    {0x00,0x00,0x00,0x00,0x00,0x76,0xCC,0xCC,0xCC,0xCC,0x7C,0x0C,0xCC,0x78,0x00,0x00}, // 103 'g'
    {0x00,0x00,0xE0,0x60,0x60,0x6C,0x76,0x66,0x66,0x66,0x66,0xE7,0x00,0x00,0x00,0x00}, // 104 'h'
    {0x00,0x00,0x18,0x18,0x00,0x78,0x18,0x18,0x18,0x18,0x18,0x7E,0x00,0x00,0x00,0x00}, // 105 'i'
    {0x00,0x00,0x0C,0x0C,0x00,0x3C,0x0C,0x0C,0x0C,0x0C,0x0C,0xCC,0xCC,0x78,0x00,0x00}, // 106 'j'
    {0x00,0x00,0xE0,0x60,0x60,0x66,0x6C,0x78,0x78,0x6C,0x66,0xE7,0x00,0x00,0x00,0x00}, // 107 'k'
    {0x00,0x00,0x78,0x18,0x18,0x18,0x18,0x18,0x18,0x18,0x18,0x7E,0x00,0x00,0x00,0x00}, // 108 'l'
    {0x00,0x00,0x00,0x00,0x00,0xFE,0xDB,0xDB,0xDB,0xDB,0xDB,0xDB,0x00,0x00,0x00,0x00}, // 109 'm'
    {0x00,0x00,0x00,0x00,0x00,0xDC,0x66,0x66,0x66,0x66,0x66,0x66,0x00,0x00,0x00,0x00}, // 110 'n'
    {0x00,0x00,0x00,0x00,0x00,0x7C,0xC6,0xC6,0xC6,0xC6,0xC6,0x7C,0x00,0x00,0x00,0x00}, // 111 'o'
    {0x00,0x00,0x00,0x00,0x00,0xDC,0x66,0x66,0x66,0x66,0x7C,0x60,0x60,0xF0,0x00,0x00}, // 112 'p'
    {0x00,0x00,0x00,0x00,0x00,0x76,0xCC,0xCC,0xCC,0xCC,0x7C,0x0C,0x0C,0x1E,0x00,0x00}, // 113 'q'
    {0x00,0x00,0x00,0x00,0x00,0xDC,0x76,0x66,0x60,0x60,0x60,0xF0,0x00,0x00,0x00,0x00}, // 114 'r'
    {0x00,0x00,0x00,0x00,0x00,0x7C,0xC6,0x70,0x1C,0x06,0xC6,0x7C,0x00,0x00,0x00,0x00}, // 115 's'
    {0x00,0x00,0x10,0x30,0x30,0xFC,0x30,0x30,0x30,0x30,0x36,0x1C,0x00,0x00,0x00,0x00}, // 116 't'
    {0x00,0x00,0x00,0x00,0x00,0xCC,0xCC,0xCC,0xCC,0xCC,0xCC,0x76,0x00,0x00,0x00,0x00}, // 117 'u'
    {0x00,0x00,0x00,0x00,0x00,0xC3,0xC3,0xC3,0xC3,0x66,0x3C,0x18,0x00,0x00,0x00,0x00}, // 118 'v'
    {0x00,0x00,0x00,0x00,0x00,0xC3,0xC3,0xC3,0xDB,0xDB,0xFF,0x66,0x00,0x00,0x00,0x00}, // 119 'w'
    {0x00,0x00,0x00,0x00,0x00,0xC3,0x66,0x3C,0x18,0x3C,0x66,0xC3,0x00,0x00,0x00,0x00}, // 120 'x'
    {0x00,0x00,0x00,0x00,0x00,0xC6,0xC6,0xC6,0xC6,0xC6,0x7E,0x06,0x0C,0xF8,0x00,0x00}, // 121 'y'
    {0x00,0x00,0x00,0x00,0x00,0xFE,0xCC,0x18,0x30,0x60,0xC6,0xFE,0x00,0x00,0x00,0x00}, // 122 'z'
};

/* Presets (Ordered: High -> Balance -> Medium -> Low) */
typedef struct {
    const char *title;
    const char *desc;
    uint32_t width;
    uint32_t height;
    uint32_t quality; // 0=Low, 1=Med, 2=High
} PresetOption;

static const PresetOption PRESETS[4] = {
    { "1. HIGH (Rata-Kanan)", "1920x1080 - Kualitas Grafik Maksimal (Full HD)", 1920, 1080, 2 },
    { "2. BALANCE",           "1600x900  - Seimbang & Tajam di TV Standar",      1600,  900, 1 },
    { "3. MEDIUM",            "1280x720  - 60 FPS Paling Stabil (Recommended)",  1280,  720, 1 },
    { "4. LOW",               "1280x720  - Mode Anti-Lag / Ringan",              1280,  720, 0 }
};

static int s_vhandle = -1;
static off_t s_vphys = -1;
static void *s_vmem = NULL;
static void *s_buffers[NUM_BUFFERS] = { NULL, NULL };
static int s_active_buf = 0;
static uint32_t *s_bg_buf = NULL;
static int s_pad_handle = -1;

/* Drawing helpers */
static void draw_rect(uint32_t *fb, int x, int y, int w, int h, uint32_t color) {
    if (!fb) return;
    for (int py = y; py < y + h; ++py) {
        if (py < 0 || py >= SCREEN_HEIGHT) continue;
        for (int px = x; px < x + w; ++px) {
            if (px < 0 || px >= SCREEN_WIDTH) continue;
            fb[py * SCREEN_WIDTH + px] = color;
        }
    }
}

static void draw_box(uint32_t *fb, int x, int y, int w, int h, int thick, uint32_t color) {
    draw_rect(fb, x, y, w, thick, color);
    draw_rect(fb, x, y + h - thick, w, thick, color);
    draw_rect(fb, x, y, thick, h, color);
    draw_rect(fb, x + w - thick, y, thick, h, color);
}

static void draw_char(uint32_t *fb, int x, int y, char c, uint32_t color, int scale) {
    if (!fb) return;
    uint8_t uc = (uint8_t)c;
    if (uc < 32 || uc > 126) uc = 32;
    const uint8_t *glyph = s_font[uc - 32];
    for (int row = 0; row < 16; ++row) {
        uint8_t bits = glyph[row];
        for (int col = 0; col < 8; ++col) {
            if (bits & (0x80 >> col)) {
                for (int sy = 0; sy < scale; ++sy) {
                    for (int sx = 0; sx < scale; ++sx) {
                        int px = x + col * scale + sx, py = y + row * scale + sy;
                        if (px >= 0 && px < SCREEN_WIDTH && py >= 0 && py < SCREEN_HEIGHT)
                            fb[py * SCREEN_WIDTH + px] = color;
                    }
                }
            }
        }
    }
}

static void draw_text(uint32_t *fb, int x, int y, const char *str, uint32_t color, int scale) {
    if (!fb || !str) return;
    int cx = x, cy = y;
    int step_x = 9 * scale;
    int step_y = 20 * scale;
    while (*str) {
        if (*str == '\n') {
            cx = x;
            cy += step_y;
        } else {
            draw_char(fb, cx, cy, *str, color, scale);
            cx += step_x;
        }
        str++;
    }
}

static void clear_frame(uint32_t *fb) {
    if (s_bg_buf) {
        memcpy(fb, s_bg_buf, FRAME_BYTES);
    } else {
        draw_rect(fb, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0xFF081220);
    }
}

/* CRC-16/XMODEM NOT Checksum for settings.dat */
static uint16_t s13_crc16(const uint8_t *data, size_t len) {
    uint32_t c = 0;
    for (size_t i = 0; i < len; ++i) {
        c ^= (uint32_t)data[i] << 8;
        for (int b = 0; b < 8; ++b) {
            c = (c & 0x8000) ? ((c << 1) ^ 0x1021) & 0xFFFF : (c << 1) & 0xFFFF;
        }
    }
    return (uint16_t)((~c) & 0xFFFF);
}

/* Save settings.dat with verified canonical structure */
static bool apply_preset(int preset_idx) {
    if (preset_idx < 0 || preset_idx >= 4) preset_idx = 2; // Default Medium

    static const uint8_t base_hdr[] = {
        'W','E','C','F', 0x02,0x00,0x00,0x00, 0x54,0x03,0x00,0x00, 0x00,0x00, 0xCB,0x00
    };
    uint8_t buf[852];
    memset(buf, 0, sizeof(buf));
    memcpy(buf, base_hdr, sizeof(base_hdr));

    uint32_t w = PRESETS[preset_idx].width;
    uint32_t h = PRESETS[preset_idx].height;
    uint32_t q = PRESETS[preset_idx].quality;

    *(uint32_t *)&buf[0x10] = w;
    *(uint32_t *)&buf[0x14] = h;
    *(uint32_t *)&buf[0x18] = 1; // 16:9
    *(uint32_t *)&buf[0x1C] = q;
    *(uint32_t *)&buf[0x20] = 1; // Fullscreen
    *(uint32_t *)&buf[0x28] = 0x166B; // Port 5739

    // Canonical XInput controller mappings
    static const uint8_t ctrl_map[] = {
        0x61,0x2b,0x1d,0x6f,0xa0,0xd5,0xcf,0x11,0xbf,0xc7,0x44,0x45,0x53,0x54,0x00,0x00,
        0x00,0x11,0x00,0x00,0x00,0x20,0x00,0x01,0x00,0x2d,0x00,0x02,0x00,0x1e,0x00,0x03,
        0x00,0x2c,0x00,0x04,0x00,0x2e,0x00,0x05,0x00,0x10,0x00,0x06,0x00,0x12,0x00,0x07,
        0x00,0x2f,0x00,0x08,0x00,0x30,0x00,0x09,0xff,0x00,0x00,0x0a,0xff,0x00,0x00,0x0b,
        0x00,0x48,0x00,0x0c,0x00,0x4d,0x00,0x0d,0x00,0x50,0x00,0x0e,0x00,0x4b,0x00,0x0f,
        0x00,0xc8,0x03,0x01,0x00,0xd0,0x02,0x01,0x00,0xcb,0x03,0x00,0x00,0xcd,0x02,0x00
    };
    if (sizeof(ctrl_map) <= 852 - 0x60) {
        memcpy(&buf[0x60], ctrl_map, sizeof(ctrl_map));
    }

    // Compute checksum
    buf[0x0C] = 0; buf[0x0D] = 0;
    uint16_t crc = s13_crc16(buf, sizeof(buf));
    buf[0x0C] = (uint8_t)(crc & 0xFF);
    buf[0x0D] = (uint8_t)((crc >> 8) & 0xFF);

    const char *paths[] = {
        "/data/prospero-win/prefixes/soccer13/drive_c/users/prospero/Documents/KONAMI/Pro Evolution Soccer 2013/settings.dat",
        "/data/prospero-win/prefixes/soccer13/drive_c/users/root/Documents/KONAMI/Pro Evolution Soccer 2013/settings.dat",
        "/data/prospero-win/settings.dat",
        NULL
    };
    bool saved_any = false;
    for (int i = 0; paths[i]; ++i) {
        int32_t fd = sceKernelOpen(paths[i], 0x0001 | 0x0200 | 0x0400, 0666); // O_WRONLY | O_CREAT | O_TRUNC
        if (fd >= 0) {
            sceKernelWrite(fd, buf, sizeof(buf));
            sceKernelClose(fd);
            saved_any = true;
        }
    }
    return saved_any;
}

/* Dynamically load required Sony userland PRX modules without static undefined references */
static bool load_userland_modules(void) {
    int res = 0;
    s_mod_user = (uint32_t)sceKernelLoadStartModule("/system/common/lib/libSceUserService.sprx", 0, NULL, 0, NULL, &res);
    if (s_mod_user & 0x80000000u)
        s_mod_user = (uint32_t)sceKernelLoadStartModule("libSceUserService.sprx", 0, NULL, 0, NULL, &res);

    s_mod_video = (uint32_t)sceKernelLoadStartModule("/system/common/lib/libSceVideoOut.sprx", 0, NULL, 0, NULL, &res);
    if (s_mod_video & 0x80000000u)
        s_mod_video = (uint32_t)sceKernelLoadStartModule("libSceVideoOut.sprx", 0, NULL, 0, NULL, &res);

    s_mod_pad = (uint32_t)sceKernelLoadStartModule("/system/common/lib/libScePad.sprx", 0, NULL, 0, NULL, &res);
    if (s_mod_pad & 0x80000000u)
        s_mod_pad = (uint32_t)sceKernelLoadStartModule("libScePad.sprx", 0, NULL, 0, NULL, &res);

    if ((s_mod_video & 0x80000000u) || (s_mod_pad & 0x80000000u)) {
        sceKernelDebugOutText(0, "s13_stub: cannot load VideoOut or Pad sprx module\n");
        return false;
    }

    sceKernelDlsym((int32_t)s_mod_video, "sceVideoOutOpen", (void **)&fn_sceVideoOutOpen);
    sceKernelDlsym((int32_t)s_mod_video, "sceVideoOutClose", (void **)&fn_sceVideoOutClose);
    sceKernelDlsym((int32_t)s_mod_video, "sceVideoOutSetFlipRate", (void **)&fn_sceVideoOutSetFlipRate);
    sceKernelDlsym((int32_t)s_mod_video, "sceVideoOutSetBufferAttribute", (void **)&fn_sceVideoOutSetBufferAttribute);
    sceKernelDlsym((int32_t)s_mod_video, "sceVideoOutRegisterBuffers", (void **)&fn_sceVideoOutRegisterBuffers);
    sceKernelDlsym((int32_t)s_mod_video, "sceVideoOutUnregisterBuffers", (void **)&fn_sceVideoOutUnregisterBuffers);
    sceKernelDlsym((int32_t)s_mod_video, "sceVideoOutSubmitFlip", (void **)&fn_sceVideoOutSubmitFlip);

    sceKernelDlsym((int32_t)s_mod_pad, "scePadInit", (void **)&fn_scePadInit);
    sceKernelDlsym((int32_t)s_mod_pad, "scePadOpen", (void **)&fn_scePadOpen);
    sceKernelDlsym((int32_t)s_mod_pad, "scePadRead", (void **)&fn_scePadRead);
    sceKernelDlsym((int32_t)s_mod_pad, "scePadClose", (void **)&fn_scePadClose);

    if (s_mod_user && !(s_mod_user & 0x80000000u)) {
        sceKernelDlsym((int32_t)s_mod_user, "sceUserServiceInitialize", (void **)&fn_sceUserServiceInitialize);
        sceKernelDlsym((int32_t)s_mod_user, "sceUserServiceGetInitialUser", (void **)&fn_sceUserServiceGetInitialUser);
    }

    return (fn_sceVideoOutOpen && fn_sceVideoOutRegisterBuffers && fn_sceVideoOutSubmitFlip &&
            fn_scePadInit && fn_scePadOpen && fn_scePadRead);
}

static void unload_userland_modules(void) {
    int res = 0;
    if (s_mod_pad && !(s_mod_pad & 0x80000000u)) {
        sceKernelStopUnloadModule((OrbisKernelModule)s_mod_pad, 0, NULL, 0, NULL, &res);
        s_mod_pad = 0;
    }
    if (s_mod_video && !(s_mod_video & 0x80000000u)) {
        sceKernelStopUnloadModule((OrbisKernelModule)s_mod_video, 0, NULL, 0, NULL, &res);
        s_mod_video = 0;
    }
    if (s_mod_user && !(s_mod_user & 0x80000000u)) {
        sceKernelStopUnloadModule((OrbisKernelModule)s_mod_user, 0, NULL, 0, NULL, &res);
        s_mod_user = 0;
    }
}

/* VideoOut setup */
static bool init_videoout(void) {
    if (!fn_sceVideoOutOpen) return false;

    s_vhandle = fn_sceVideoOutOpen(ORBIS_VIDEO_USER_MAIN, ORBIS_VIDEO_OUT_BUS_MAIN, 0, NULL);
    if (s_vhandle < 0 && fn_sceUserServiceInitialize && fn_sceUserServiceGetInitialUser) {
        fn_sceUserServiceInitialize(NULL);
        int32_t user = -1;
        if (fn_sceUserServiceGetInitialUser(&user) >= 0 && user >= 0)
            s_vhandle = fn_sceVideoOutOpen(user, ORBIS_VIDEO_OUT_BUS_MAIN, 0, NULL);
    }
    if (s_vhandle < 0) return false;

    size_t pool = sceKernelGetDirectMemorySize();
    if (pool < TOTAL_VMEM) return false;

    if (sceKernelAllocateDirectMemory(0, (int64_t)pool, TOTAL_VMEM, DIRECT_ALIGN, DIRECT_TYPE, &s_vphys) < 0)
        return false;

    if (sceKernelMapDirectMemory(&s_vmem, TOTAL_VMEM, 0x33, 0, s_vphys, DIRECT_ALIGN) < 0)
        return false;

    memset(s_vmem, 0, TOTAL_VMEM);
    s_buffers[0] = s_vmem;
    s_buffers[1] = (uint8_t *)s_vmem + FRAME_BYTES;

    if (fn_sceVideoOutSetFlipRate)
        fn_sceVideoOutSetFlipRate(s_vhandle, ORBIS_VIDEO_OUT_FLIP_60HZ);

    OrbisVideoOutBufferAttribute attr;
    memset(&attr, 0, sizeof(attr));
    fn_sceVideoOutSetBufferAttribute(&attr, PIXEL_FORMAT, ORBIS_VIDEO_OUT_TILING_MODE_LINEAR,
                                     ORBIS_VIDEO_OUT_ASPECT_RATIO_16_9, SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_WIDTH);
    if (fn_sceVideoOutRegisterBuffers(s_vhandle, 0, s_buffers, NUM_BUFFERS, &attr) < 0)
        return false;

    // Load darkened background buffer
    s_bg_buf = (uint32_t *)mmap(NULL, FRAME_BYTES, PROT_READ | PROT_WRITE,
                                MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (s_bg_buf != MAP_FAILED) {
        int32_t fd = sceKernelOpen("/app0/app/assets/bg.raw", 0, 0);
        if (fd < 0) fd = sceKernelOpen("/data/prospero-win/bg.raw", 0, 0);
        if (fd >= 0) {
            sceKernelRead(fd, s_bg_buf, FRAME_BYTES);
            sceKernelClose(fd);
        } else {
            munmap(s_bg_buf, FRAME_BYTES);
            s_bg_buf = NULL;
        }
    } else {
        s_bg_buf = NULL;
    }

    return true;
}

static void flip_screen(void) {
    if (s_vhandle < 0 || !fn_sceVideoOutSubmitFlip) return;
    fn_sceVideoOutSubmitFlip(s_vhandle, s_active_buf, ORBIS_VIDEO_OUT_FLIP_VSYNC, 0);
    s_active_buf = (s_active_buf + 1) % NUM_BUFFERS;
}

static void shutdown_videoout(void) {
    if (s_bg_buf && s_bg_buf != MAP_FAILED) {
        munmap(s_bg_buf, FRAME_BYTES);
        s_bg_buf = NULL;
    }
    if (s_vhandle >= 0 && fn_sceVideoOutClose) {
        if (fn_sceVideoOutUnregisterBuffers)
            fn_sceVideoOutUnregisterBuffers(s_vhandle, 0);
        fn_sceVideoOutClose(s_vhandle);
        s_vhandle = -1;
    }
    if (s_vmem) {
        sceKernelMunmap(s_vmem, TOTAL_VMEM);
        s_vmem = NULL;
    }
    if (s_vphys >= 0) {
        sceKernelReleaseDirectMemory(s_vphys, TOTAL_VMEM);
        s_vphys = -1;
    }
}

/* Pad setup */
static bool init_pad(void) {
    if (!fn_scePadInit || !fn_scePadOpen) return false;
    fn_scePadInit();

    int32_t user = -1;
    if (fn_sceUserServiceGetInitialUser)
        fn_sceUserServiceGetInitialUser(&user);
    if (user < 0) user = 0;

    s_pad_handle = fn_scePadOpen(user, 0, 0, NULL);
    return (s_pad_handle >= 0);
}

static void shutdown_pad(void) {
    if (s_pad_handle >= 0 && fn_scePadClose) {
        fn_scePadClose(s_pad_handle);
        s_pad_handle = -1;
    }
}

/* Render Model 1 Menu */
static void render_menu(uint32_t *fb, int selected_idx) {
    clear_frame(fb);

    // Center Card Dimensions
    int cw = 1100, ch = 680;
    int cx = (SCREEN_WIDTH - cw) / 2;
    int cy = (SCREEN_HEIGHT - ch) / 2;

    // Dark Card Overlay with Blue PS Border
    draw_rect(fb, cx, cy, cw, ch, 0xD00A111E);
    draw_box(fb, cx, cy, cw, ch, 3, 0xFF2A82E4);

    // Header Title
    draw_text(fb, cx + 420, cy + 40, "SOCCER 13", 0xFFFFFFFF, 3);
    draw_text(fb, cx + 370, cy + 105, "GRAPHICS PRESET SELECTION", 0xFF00FFCC, 1);
    draw_rect(fb, cx + 50, cy + 135, cw - 100, 2, 0xFF1D5A9C);

    // Vertical Preset List
    for (int i = 0; i < 4; ++i) {
        int iy = cy + 170 + i * 105;
        bool sel = (selected_idx == i);

        if (sel) {
            draw_rect(fb, cx + 70, iy, cw - 140, 80, 0xFF185599);
            draw_box(fb, cx + 70, iy, cw - 140, 80, 2, 0xFF00D4FF);
            draw_text(fb, cx + 90, iy + 16, ">", 0xFF00FFCC, 2);
            draw_text(fb, cx + 130, iy + 14, PRESETS[i].title, 0xFFFFFFFF, 2);
            draw_text(fb, cx + 130, iy + 48, PRESETS[i].desc, 0xFF00FFCC, 1);
        } else {
            draw_rect(fb, cx + 70, iy, cw - 140, 80, 0x80101C2E);
            draw_box(fb, cx + 70, iy, cw - 140, 80, 1, 0xFF224466);
            draw_text(fb, cx + 130, iy + 14, PRESETS[i].title, 0xFFAAAAAA, 2);
            draw_text(fb, cx + 130, iy + 48, PRESETS[i].desc, 0xFF6688AA, 1);
        }
    }

    // Help Footer
    draw_rect(fb, cx + 50, cy + ch - 65, cw - 100, 1, 0xFF1D5A9C);
    draw_text(fb, cx + 240, cy + ch - 45, "[D-PAD UP/DOWN] Pilih    |    [CROSS] Terapkan & Main", 0xFF88BBEE, 1);
}

/* Run the vertical interactive selector */
static int run_selector(void) {
    if (!load_userland_modules()) {
        sceKernelDebugOutText(0, "s13_stub: fallback to default 720p\n");
        apply_preset(2); // Medium 720p
        return 2;
    }

    if (!init_videoout()) {
        sceKernelDebugOutText(0, "s13_stub: init_videoout failed, fallback\n");
        apply_preset(2);
        unload_userland_modules();
        return 2;
    }

    init_pad();

    int selected = 2; // Default to 3. MEDIUM (Recommended)
    uint32_t prev_buttons = 0;
    bool running = true;

    while (running) {
        uint32_t buttons = 0;
        if (s_pad_handle >= 0 && fn_scePadRead) {
            OrbisPadData pdata;
            if (fn_scePadRead(s_pad_handle, &pdata, 1) > 0) {
                buttons = pdata.buttons;
                if (pdata.leftStick.y < 64)  buttons |= ORBIS_PAD_BUTTON_UP;
                if (pdata.leftStick.y > 192) buttons |= ORBIS_PAD_BUTTON_DOWN;
            }
        }

        uint32_t pressed = buttons & ~prev_buttons;
        prev_buttons = buttons;

        if (pressed & ORBIS_PAD_BUTTON_UP) {
            selected = (selected + 3) % 4;
        }
        if (pressed & ORBIS_PAD_BUTTON_DOWN) {
            selected = (selected + 1) % 4;
        }
        if (pressed & (ORBIS_PAD_BUTTON_CROSS | ORBIS_PAD_BUTTON_OPTIONS)) {
            // Apply chosen preset
            apply_preset(selected);

            // Display loading transition
            uint32_t *fb = (uint32_t *)s_buffers[s_active_buf];
            render_menu(fb, selected);
            int cx = (SCREEN_WIDTH - 1100) / 2;
            int cy = (SCREEN_HEIGHT - 680) / 2;
            draw_rect(fb, cx + 70, cy + 680 - 64, 1100 - 140, 36, 0xFF003366);
            draw_text(fb, cx + 280, cy + 680 - 55, "Menerapkan Preset... Memuat SOCCER 13!", 0xFF00FFCC, 1);
            flip_screen();
            sceKernelUsleep(300000); // 300ms visual confirmation
            running = false;
            break;
        }

        // Render Frame
        uint32_t *fb = (uint32_t *)s_buffers[s_active_buf];
        render_menu(fb, selected);
        flip_screen();

        sceKernelUsleep(16666); // ~60 FPS
    }

    shutdown_pad();
    shutdown_videoout();
    unload_userland_modules();
    return selected;
}

/* Handoff to relocated_wine_app.prx */
static int segments(int32_t handle, Segment out[MAX_SEGMENTS], uint32_t *count) {
    uint8_t raw[MODULE_INFO_BYTES] __attribute__((aligned(16)));
    memset(raw, 0, sizeof(raw));
    *(uint64_t *)raw = sizeof(raw);
    int rc = sceKernelGetModuleInfo((OrbisKernelModule)handle, (OrbisKernelModuleInfo *)raw);
    if (rc < 0) return rc;
    uint32_t n;
    memcpy(&n, raw + 0x148, sizeof(n));
    if (!n || n > MAX_SEGMENTS) return -1;
    for (uint32_t i = 0; i < n; ++i) {
        uint8_t *item = raw + 0x108 + i * 16;
        uint64_t address;
        memcpy(&address, item, 8);
        memcpy(&out[i].size, item + 8, 4);
        memcpy(&out[i].protection, item + 12, 4);
        out[i].address = (const void *)(uintptr_t)address;
        if (!address || !out[i].size) return -1;
    }
    *count = n;
    return 0;
}

static const Descriptor *find_descriptor(const Segment *items, uint32_t count) {
    for (uint32_t s = 0; s < count; ++s) {
        const uint8_t *base = items[s].address;
        if (!(items[s].protection & 1u)) continue;
        for (size_t off = 0; off + 16 <= items[s].size; off += 16) {
            uint64_t magic;
            memcpy(&magic, base + off, sizeof(magic));
            if (magic != PRX_MAGIC) continue;
            const Descriptor *d = (const Descriptor *)(base + off);
            if (d->version == 1 && d->count && d->count <= MAX_EXPORTS &&
                off + 16 + d->count * sizeof(Export) <= items[s].size)
                return d;
        }
    }
    return NULL;
}

int main(int argc, char **argv) {
    (void)argc;
    sceKernelDebugOutText(0, "s13_stub: SOCCER 13 Model 1 Launcher Active\n");

    // 1. Run interactive vertical graphics preset selector
    run_selector();

    // 2. Load relocated_wine_app.prx
    int result = 0;
    uint32_t handle = sceKernelLoadStartModule("/app0/sce_module/relocated_wine_app.prx", 0, NULL, 0, NULL, &result);
    if (handle & 0x80000000u) {
        char line[128];
        snprintf(line, sizeof(line), "relocwine: app PRX load failed handle=0x%x result=0x%x\n", handle, result);
        sceKernelDebugOutText(0, line);
        for (;;) sceKernelUsleep(1000000);
    }

    Segment items[MAX_SEGMENTS];
    uint32_t count = 0;
    const Descriptor *d = NULL;
    if (!segments((int32_t)handle, items, &count)) d = find_descriptor(items, count);
    Entry entry = NULL;
    if (d) for (uint32_t i = 0; i < d->count; ++i)
        if (!strcmp(d->exports[i].name, "pw_relocated_wine_start"))
            entry = (Entry)d->exports[i].address;

    if (!entry) {
        sceKernelDebugOutText(0, "relocwine: PRX entry descriptor missing\n");
        for (;;) sceKernelUsleep(1000000);
    }

    sceKernelDebugOutText(0, "relocwine: entering high-address Wine PRX (direct game mode: soccer13)\n");

    /* Direct boot into soccer13 game mode */
    char *game_argv[] = { (argv && argv[0]) ? argv[0] : "/app0/eboot.bin", "game", "soccer13", NULL };
    entry(3, game_argv);

    for (;;) sceKernelUsleep(1000000);
}
