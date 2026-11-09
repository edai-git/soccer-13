#pragma once

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

#define S13_SCREEN_WIDTH  1920
#define S13_SCREEN_HEIGHT 1080

// ARGB 32-bit color helper
#define S13_COLOR(a, r, g, b) (((uint32_t)(a) << 24) | ((uint32_t)(r) << 16) | ((uint32_t)(g) << 8) | ((uint32_t)(b)))

#define S13_COLOR_BG       S13_COLOR(0xFF, 0x0A, 0x11, 0x24) // Deep Navy
#define S13_COLOR_PANEL    S13_COLOR(0xFF, 0x13, 0x1C, 0x38) // Card Background
#define S13_COLOR_HEADER   S13_COLOR(0xFF, 0x1C, 0x2A, 0x4D) // Header Bar
#define S13_COLOR_TEXT     S13_COLOR(0xFF, 0xEE, 0xF2, 0xF7) // Bright White
#define S13_COLOR_MUTED    S13_COLOR(0xFF, 0x8A, 0x9B, 0xB5) // Secondary Gray/Blue
#define S13_COLOR_ACCENT   S13_COLOR(0xFF, 0x00, 0x99, 0xFF) // Neon Cyan/Blue
#define S13_COLOR_SUCCESS  S13_COLOR(0xFF, 0x2E, 0xCC, 0x71) // Green
#define S13_COLOR_WARNING  S13_COLOR(0xFF, 0xF3, 0x9C, 0x12) // Orange
#define S13_COLOR_ERROR    S13_COLOR(0xFF, 0xE7, 0x4C, 0x3C) // Red

bool s13_video_init(void);
bool s13_video_load_bg(const char *path);
void s13_video_clear(uint32_t color);
void s13_video_draw_rect(int x, int y, int w, int h, uint32_t color);
void s13_video_draw_box(int x, int y, int w, int h, int thickness, uint32_t color);
void s13_video_draw_char(int x, int y, char c, uint32_t color);
void s13_video_draw_text(int x, int y, const char *text, uint32_t color);
void s13_video_flip(void);
void s13_video_shutdown(void);

#ifdef __cplusplus
}
#endif

