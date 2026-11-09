#pragma once

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

#define S13_SETTINGS_DAT_SIZE 852

typedef struct {
    uint32_t width;
    uint32_t height;
    uint32_t quality;    // 0 = Low, 1 = Medium, 2 = High
    uint32_t fullscreen; // 0 = Windowed, 1 = Fullscreen
    bool xinput;         // true = 0xCB flags, false = 0xC3
    bool vsync;
    bool valid;
} s13_game_settings_t;

// Loads settings from prefix path
bool s13_settings_load(const char *path, s13_game_settings_t *out);

// Saves settings calculating CRC16-XMODEM bitwise NOT
bool s13_settings_save(const char *path, const s13_game_settings_t *in);

// Calculates CRC16/XMODEM NOT with checksum offset 0x0C/0x0D zeroed
uint16_t s13_crc16_not(const uint8_t *data, size_t len);

#ifdef __cplusplus
}
#endif

