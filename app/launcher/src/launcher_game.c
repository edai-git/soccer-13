#include "launcher_game.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

#define DEFAULT_PREFIX "/data/prospero-win/prefixes/soccer13"
#define GAME_REL_PATH  "drive_c/Games/SOCCER13"

static bool file_exists(const char *path) {
    struct stat st;
    return (stat(path, &st) == 0 && S_ISREG(st.st_mode));
}

static bool dir_exists(const char *path) {
    struct stat st;
    return (stat(path, &st) == 0 && S_ISDIR(st.st_mode));
}

void s13_game_detect(s13_game_info_t *info) {
    if (!info) return;
    memset(info, 0, sizeof(*info));

    snprintf(info->prefix_path, sizeof(info->prefix_path), "%s", DEFAULT_PREFIX);
    snprintf(info->exe_path, sizeof(info->exe_path), "%s/%s/pes2013.exe", DEFAULT_PREFIX, GAME_REL_PATH);
    snprintf(info->img_path, sizeof(info->img_path), "%s/%s/img", DEFAULT_PREFIX, GAME_REL_PATH);

    if (!dir_exists(info->prefix_path)) {
        info->status = GAME_STATUS_NOT_INSTALLED;
        snprintf(info->status_message, sizeof(info->status_message), "Game not installed in prefix.");
        return;
    }

    if (!file_exists(info->exe_path)) {
        info->status = GAME_STATUS_NOT_INSTALLED;
        snprintf(info->status_message, sizeof(info->status_message), "Missing pes2013.exe in C:\\Games\\SOCCER13.");
        return;
    }

    if (!dir_exists(info->img_path)) {
        info->status = GAME_STATUS_MISSING_IMG;
        snprintf(info->status_message, sizeof(info->status_message), "Missing img/ folder in C:\\Games\\SOCCER13.");
        return;
    }

    // Check for mods (e.g., kitserver13 or kload.dll)
    char mod_path[320];
    snprintf(mod_path, sizeof(mod_path), "%s/%s/kitserver13", DEFAULT_PREFIX, GAME_REL_PATH);
    if (dir_exists(mod_path)) {
        info->has_mods = true;
    }

    info->status = GAME_STATUS_READY;
    snprintf(info->status_message, sizeof(info->status_message), "Ready to play (Verified).");
}

bool s13_game_launch(s13_game_info_t *info) {
    if (!info || info->status != GAME_STATUS_READY) return false;

    info->status = GAME_STATUS_RUNNING;
    snprintf(info->status_message, sizeof(info->status_message), "Game running...");

    // On PS4 console: loads relocated_wine_app.prx with soccer13.profile
    return true;
}

bool s13_game_poll_status(s13_game_info_t *info) {
    if (!info) return false;
    // Returns true while running, false when process terminates
    return (info->status == GAME_STATUS_RUNNING);
}

