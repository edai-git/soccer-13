#pragma once

#include <stddef.h>
#include <stdbool.h>
#include "launcher_game.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    char usb_path[64];
    bool source_found;
    bool has_repack;
    bool has_mods;
    int files_staged;
    int saves_preserved;
    char error_message[256];
} s13_install_result_t;

// Scans /mnt/usb0 through /mnt/usb7 for game files
bool s13_install_scan_usb(char *out_usb_path, size_t max_len);

// Executes installation from USB/source directory to prefix
bool s13_install_run(const char *source_dir, bool repair_mode, s13_install_result_t *out);

// Save backup / restore
bool s13_save_backup(const char *dest_dir);
bool s13_save_restore(const char *src_dir);

#ifdef __cplusplus
}
#endif

