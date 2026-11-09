#include "launcher_settings.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define WIDTH_OFFSET      0x10
#define HEIGHT_OFFSET     0x14
#define QUALITY_OFFSET    0x1C
#define FULLSCREEN_OFFSET 0x20
#define CHECKSUM_OFFSET   0x0C
#define FLAGS_OFFSET      0x0E

uint16_t s13_crc16_not(const uint8_t *data, size_t len) {
    uint32_t c = 0;
    for (size_t i = 0; i < len; ++i) {
        c ^= (uint32_t)data[i] << 8;
        for (int b = 0; b < 8; ++b) {
            c = (c & 0x8000) ? ((c << 1) ^ 0x1021) & 0xFFFF : (c << 1) & 0xFFFF;
        }
    }
    return (uint16_t)((~c) & 0xFFFF);
}

bool s13_settings_load(const char *path, s13_game_settings_t *out) {
    if (!path || !out) return false;
    memset(out, 0, sizeof(*out));

    FILE *f = fopen(path, "rb");
    if (!f) return false;

    uint8_t buf[S13_SETTINGS_DAT_SIZE];
    size_t read_bytes = fread(buf, 1, sizeof(buf), f);
    fclose(f);

    if (read_bytes != S13_SETTINGS_DAT_SIZE) return false;
    if (memcmp(buf, "WECF", 4) != 0) return false;

    // Verify CRC
    uint16_t stored_crc = (uint16_t)buf[CHECKSUM_OFFSET] | ((uint16_t)buf[CHECKSUM_OFFSET + 1] << 8);
    buf[CHECKSUM_OFFSET] = 0;
    buf[CHECKSUM_OFFSET + 1] = 0;
    uint16_t computed_crc = s13_crc16_not(buf, sizeof(buf));

    if (stored_crc != computed_crc) {
        out->valid = false;
        return false;
    }

    out->width = *(uint32_t *)&buf[WIDTH_OFFSET];
    out->height = *(uint32_t *)&buf[HEIGHT_OFFSET];
    out->quality = *(uint32_t *)&buf[QUALITY_OFFSET];
    out->fullscreen = *(uint32_t *)&buf[FULLSCREEN_OFFSET];
    uint16_t flags = *(uint16_t *)&buf[FLAGS_OFFSET];
    out->xinput = (flags & 0x08) != 0;
    out->vsync = (flags & 0x01) != 0;
    out->valid = true;
    return true;
}

bool s13_settings_save(const char *path, const s13_game_settings_t *in) {
    if (!path || !in) return false;

    uint8_t buf[S13_SETTINGS_DAT_SIZE];
    memset(buf, 0, sizeof(buf));

    // Base header: "WECF\x02\x00\x00\x00\x54\x03\x00\x00"
    memcpy(buf, "WECF", 4);
    *(uint32_t *)&buf[4] = 2;                         // Version 2
    *(uint32_t *)&buf[8] = S13_SETTINGS_DAT_SIZE;     // 852 bytes

    *(uint32_t *)&buf[WIDTH_OFFSET] = in->width;
    *(uint32_t *)&buf[HEIGHT_OFFSET] = in->height;
    *(uint32_t *)&buf[0x18] = 1;                      // 16:9 aspect ratio
    *(uint32_t *)&buf[QUALITY_OFFSET] = in->quality;
    *(uint32_t *)&buf[FULLSCREEN_OFFSET] = in->fullscreen;
    *(uint32_t *)&buf[0x28] = 0x166B;                 // Port 5739

    uint16_t flags = in->xinput ? 0x00CB : 0x00C3;
    *(uint16_t *)&buf[FLAGS_OFFSET] = flags;

    // Calculate CRC with checksum zeroed
    buf[CHECKSUM_OFFSET] = 0;
    buf[CHECKSUM_OFFSET + 1] = 0;
    uint16_t crc = s13_crc16_not(buf, sizeof(buf));
    buf[CHECKSUM_OFFSET] = (uint8_t)(crc & 0xFF);
    buf[CHECKSUM_OFFSET + 1] = (uint8_t)((crc >> 8) & 0xFF);

    FILE *f = fopen(path, "wb");
    if (!f) return false;
    size_t written = fwrite(buf, 1, sizeof(buf), f);
    fclose(f);

    return written == sizeof(buf);
}

