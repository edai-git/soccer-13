#pragma once

#include "launcher_input.h"
#include "launcher_game.h"
#include "launcher_settings.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    VIEW_MAIN_MENU = 0,
    VIEW_SETTINGS,
    VIEW_INSTALL_REPAIR,
    VIEW_SAVE_BACKUP,
    VIEW_ABOUT,
    VIEW_LOG_VIEWER
} s13_view_t;

typedef struct {
    s13_view_t current_view;
    int selected_item;
    s13_game_info_t game_info;
    s13_game_settings_t settings;
    bool should_exit;
    char notice_message[128];
    uint32_t notice_color;
} s13_ui_state_t;

void s13_ui_init(s13_ui_state_t *ui);
void s13_ui_update(s13_ui_state_t *ui, const s13_input_state_t *input);
void s13_ui_render(const s13_ui_state_t *ui);

#ifdef __cplusplus
}
#endif
