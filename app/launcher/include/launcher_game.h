#pragma once

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    GAME_STATUS_UNKNOWN = 0,
    GAME_STATUS_NOT_INSTALLED,
    GAME_STATUS_READY,
    GAME_STATUS_MISSING_IMG,
    GAME_STATUS_RUNNING,
    GAME_STATUS_CRASHED
} s13_game_status_t;

typedef struct {
    s13_game_status_t status;
    char status_message[256];
    char exe_path[256];
    char prefix_path[256];
    char img_path[256];
    int img_count;
    bool has_mods;
    int last_exit_code;
} s13_game_info_t;

// Checks installation in prefix (/data/prospero-win/prefixes/soccer13)
void s13_game_detect(s13_game_info_t *info);

// Spawns Wine runtime via orbis-win relocated_wine_app.prx
bool s13_game_launch(s13_game_info_t *info);

// Monitors process status
bool s13_game_poll_status(s13_game_info_t *info);

#ifdef __cplusplus
}
#endif
