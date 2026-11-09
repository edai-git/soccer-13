/* app/launcher/src/handoff_stub.c — SOCCER 13 Direct Autoboot Stub
 * Automatically configures PES 2013 to High Preset (1080p, High Quality, VSync ON),
 * and directly boots into the game without showing the Bliss launcher screen.
 * Strictly adheres to no-RELRO layout and libkernel-only dynamic imports.
 */

#include <orbis/libkernel.h>
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

static const char *const libkernel_symbols[] __attribute__((unused)) = {
#include "libkernel-symbols.inc"
};

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

/* Save canonical 852-byte settings.dat using pure libkernel syscalls */
static bool apply_preset(int width, int height, int quality) {
    static const uint8_t base_hdr[] = {
        'W','E','C','F', 0x02,0x00,0x00,0x00, 0x54,0x03,0x00,0x00, 0x00,0x00, 0xCB,0x00
    };
    uint8_t buf[852];
    memset(buf, 0, sizeof(buf));
    memcpy(buf, base_hdr, sizeof(base_hdr));

    *(uint32_t *)&buf[0x10] = (uint32_t)width;
    *(uint32_t *)&buf[0x14] = (uint32_t)height;
    *(uint32_t *)&buf[0x18] = 1; // 16:9
    *(uint32_t *)&buf[0x1C] = (uint32_t)quality;
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
        int32_t fd = sceKernelOpen(paths[i], 0x0001 | 0x0200 | 0x0400, 0666);
        if (fd >= 0) {
            sceKernelWrite(fd, buf, sizeof(buf));
            sceKernelClose(fd);
            saved_any = true;
        }
    }
    return saved_any;
}

static void diagnose_libkernel(void) {
    OrbisKernelModule modules[256];
    size_t available = 0;
    int rc = sceKernelGetModuleList(modules, sizeof(modules) / sizeof(modules[0]), &available);
    if (rc != 0) return;

    size_t count = available < sizeof(modules) / sizeof(modules[0]) ?
                   available : sizeof(modules) / sizeof(modules[0]);
    for (size_t i = 0; i < count; ++i) {
        OrbisKernelModuleInfo info;
        memset(&info, 0, sizeof(info));
        info.size = sizeof(info);
        if (sceKernelGetModuleInfo(modules[i], &info) == 0 && strstr(info.name, "libkernel")) {
            sceKernelDebugOutText(0, "s13_stub: libkernel found\n");
            break;
        }
    }
}

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
    sceKernelDebugOutText(0, "s13_stub: SOCCER 13 Direct Autoboot (HIGH 1080p)\n");

    // 1. Write High Preset (1920x1080 Full HD, High Quality)
    apply_preset(1920, 1080, 2);

    diagnose_libkernel();

    // 2. Load relocated_wine_app.prx into high memory
    int result = 0;
    uint32_t handle = sceKernelLoadStartModule(
        "/app0/sce_module/relocated_wine_app.prx", 0, NULL, 0, NULL, &result);
    if (handle & 0x80000000u) {
        char line[128];
        snprintf(line, sizeof(line),
                 "relocwine: app PRX load failed handle=0x%x result=0x%x\n",
                 handle, result);
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

    // 3. Direct autoboot into soccer13 game mode
    char *game_argv[] = {
        (argv && argv[0]) ? argv[0] : "/app0/eboot.bin",
        "profile=soccer13",
        "path=C:\\Games\\SOCCER13\\pes2013.exe",
        NULL
    };
    entry(3, game_argv);

    for (;;) sceKernelUsleep(1000000);
}
