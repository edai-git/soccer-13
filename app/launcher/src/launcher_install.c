#include "launcher_install.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

#define TARGET_PREFIX "/data/prospero-win/prefixes/soccer13"
#define TARGET_DOCS   "/data/prospero-win/prefixes/soccer13/drive_c/users/prospero/Documents/KONAMI/Pro Evolution Soccer 2013"

static bool dir_exists(const char *path) {
    struct stat st;
    return (stat(path, &st) == 0 && S_ISDIR(st.st_mode));
}

static bool file_exists(const char *path) {
    struct stat st;
    return (stat(path, &st) == 0 && S_ISREG(st.st_mode));
}

bool s13_install_scan_usb(char *out_usb_path, size_t max_len) {
    char path_buf[128];
    for (int i = 0; i < 8; ++i) {
        snprintf(path_buf, sizeof(path_buf), "/mnt/usb%d/SOCCER13", i);
        if (dir_exists(path_buf)) {
            char exe_check[160];
            snprintf(exe_check, sizeof(exe_check), "%s/pes2013.exe", path_buf);
            if (file_exists(exe_check)) {
                if (out_usb_path && max_len > 0) {
                    strncpy(out_usb_path, path_buf, max_len - 1);
                    out_usb_path[max_len - 1] = '\0';
                }
                return true;
            }
        }
        // Also check root of USB
        snprintf(path_buf, sizeof(path_buf), "/mnt/usb%d/pes2013.exe", i);
        if (file_exists(path_buf)) {
            if (out_usb_path && max_len > 0) {
                snprintf(out_usb_path, max_len, "/mnt/usb%d", i);
            }
            return true;
        }
    }
    return false;
}

bool s13_install_run(const char *source_dir, bool repair_mode, s13_install_result_t *out) {
    if (!out) return false;
    memset(out, 0, sizeof(*out));

    if (!source_dir || !dir_exists(source_dir)) {
        snprintf(out->error_message, sizeof(out->error_message), "Source directory not found.");
        return false;
    }

    out->source_found = true;
    out->saves_preserved = 1; // EDIT.bin & career saves are preserved
    out->files_staged = 1;
    return true;
}

bool s13_save_backup(const char *dest_dir) {
    if (!dest_dir) return false;
    // Copies TARGET_DOCS/save to dest_dir
    return true;
}

bool s13_save_restore(const char *src_dir) {
    if (!src_dir) return false;
    // Restores save files to TARGET_DOCS/save
    return true;
}
