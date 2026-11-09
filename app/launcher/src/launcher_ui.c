#include "launcher_ui.h"
#include "launcher_video.h"
#include "launcher_install.h"
#include <stdio.h>
#include <string.h>

static const char *s_resolutions[] = {"1280x720 (720p)", "1600x900 (900p)", "1920x1080 (1080p)"};
static const uint32_t s_res_widths[] = {1280, 1600, 1920};
static const uint32_t s_res_heights[] = {720, 900, 1080};
static const char *s_qualities[] = {"Low", "Medium (Default)", "High"};

void s13_ui_init(s13_ui_state_t *ui) {
    if (!ui) return;
    memset(ui, 0, sizeof(*ui));
    ui->current_view = VIEW_MAIN_MENU;
    ui->selected_item = 0;

    // Detect game status
    s13_game_detect(&ui->game_info);

    // Initialize default settings (720p Medium Fullscreen)
    ui->settings.width = 1280;
    ui->settings.height = 720;
    ui->settings.quality = 1;
    ui->settings.fullscreen = 1;
    ui->settings.xinput = true;
    ui->settings.vsync = true;
    ui->settings.valid = true;

    // Try to load existing settings.dat from prefix
    char settings_path[320];
    snprintf(settings_path, sizeof(settings_path), "%s/drive_c/users/prospero/Documents/KONAMI/Pro Evolution Soccer 2013/settings.dat", ui->game_info.prefix_path);
    s13_settings_load(settings_path, &ui->settings);

    snprintf(ui->notice_message, sizeof(ui->notice_message), "Welcome to SOCCER13 Launcher");
    ui->notice_color = S13_COLOR_MUTED;
}

void s13_ui_update(s13_ui_state_t *ui, const s13_input_state_t *input) {
    if (!ui || !input) return;

    if (ui->current_view == VIEW_MAIN_MENU) {
        if (input->buttons_pressed & S13_PAD_UP) {
            ui->selected_item = (ui->selected_item > 0) ? ui->selected_item - 1 : 4;
        } else if (input->buttons_pressed & S13_PAD_DOWN) {
            ui->selected_item = (ui->selected_item < 4) ? ui->selected_item + 1 : 0;
        }

        if (input->buttons_pressed & S13_PAD_CROSS) {
            switch (ui->selected_item) {
                case 0: // PLAY
                    if (ui->game_info.status == GAME_STATUS_READY) {
                        s13_game_launch(&ui->game_info);
                        snprintf(ui->notice_message, sizeof(ui->notice_message), "Launching game...");
                        ui->notice_color = S13_COLOR_SUCCESS;
                    } else {
                        snprintf(ui->notice_message, sizeof(ui->notice_message), "Cannot launch: %s", ui->game_info.status_message);
                        ui->notice_color = S13_COLOR_ERROR;
                    }
                    break;
                case 1: // SETTINGS
                    ui->current_view = VIEW_SETTINGS;
                    ui->selected_item = 0;
                    break;
                case 2: // INSTALL / REPAIR
                    ui->current_view = VIEW_INSTALL_REPAIR;
                    ui->selected_item = 0;
                    break;
                case 3: // BACKUP / RESTORE
                    ui->current_view = VIEW_SAVE_BACKUP;
                    ui->selected_item = 0;
                    break;
                case 4: // ABOUT
                    ui->current_view = VIEW_ABOUT;
                    ui->selected_item = 0;
                    break;
            }
        }

        // Quick button actions
        if (input->buttons_pressed & S13_PAD_TRIANGLE) {
            ui->current_view = VIEW_LOG_VIEWER;
        }
        if (input->buttons_pressed & S13_PAD_CIRCLE) {
            ui->should_exit = true;
        }

    } else if (ui->current_view == VIEW_SETTINGS) {
        if (input->buttons_pressed & S13_PAD_UP) {
            ui->selected_item = (ui->selected_item > 0) ? ui->selected_item - 1 : 3;
        } else if (input->buttons_pressed & S13_PAD_DOWN) {
            ui->selected_item = (ui->selected_item < 3) ? ui->selected_item + 1 : 0;
        }

        // Horizontal toggle
        if (ui->selected_item == 0) { // Resolution
            int current_idx = (ui->settings.width == 1920) ? 2 : (ui->settings.width == 1600 ? 1 : 0);
            if (input->buttons_pressed & S13_PAD_RIGHT) current_idx = (current_idx + 1) % 3;
            if (input->buttons_pressed & S13_PAD_LEFT) current_idx = (current_idx + 2) % 3;
            ui->settings.width = s_res_widths[current_idx];
            ui->settings.height = s_res_heights[current_idx];
        } else if (ui->selected_item == 1) { // Quality
            int q = (int)ui->settings.quality;
            if (input->buttons_pressed & S13_PAD_RIGHT) q = (q + 1) % 3;
            if (input->buttons_pressed & S13_PAD_LEFT) q = (q + 2) % 3;
            ui->settings.quality = (uint32_t)q;
        } else if (ui->selected_item == 2) { // Fullscreen
            if (input->buttons_pressed & (S13_PAD_LEFT | S13_PAD_RIGHT)) {
                ui->settings.fullscreen = !ui->settings.fullscreen;
            }
        }

        if (input->buttons_pressed & S13_PAD_CROSS) { // Save
            char settings_path[320];
            snprintf(settings_path, sizeof(settings_path), "%s/drive_c/users/prospero/Documents/KONAMI/Pro Evolution Soccer 2013/settings.dat", ui->game_info.prefix_path);
            if (s13_settings_save(settings_path, &ui->settings)) {
                snprintf(ui->notice_message, sizeof(ui->notice_message), "Settings saved successfully (CRC OK)");
                ui->notice_color = S13_COLOR_SUCCESS;
            } else {
                snprintf(ui->notice_message, sizeof(ui->notice_message), "Failed to save settings.dat");
                ui->notice_color = S13_COLOR_ERROR;
            }
            ui->current_view = VIEW_MAIN_MENU;
            ui->selected_item = 1;
        }

        if (input->buttons_pressed & S13_PAD_CIRCLE) {
            ui->current_view = VIEW_MAIN_MENU;
            ui->selected_item = 1;
        }

    } else { // Generic Back for Subviews
        if (input->buttons_pressed & S13_PAD_CIRCLE) {
            ui->current_view = VIEW_MAIN_MENU;
            ui->selected_item = 0;
        }
    }
}

void s13_ui_render(const s13_ui_state_t *ui) {
    if (!ui) return;

    // Background
    s13_video_clear(S13_COLOR_BG);

    // Header bar
    s13_video_draw_rect(0, 0, S13_SCREEN_WIDTH, 80, S13_COLOR_HEADER);
    s13_video_draw_text(60, 28, "SOCCER13  ::  PLAYSTATION 4 HEN LAUNCHER", S13_COLOR_ACCENT);

    // Status Panel
    s13_video_draw_rect(60, 120, 1800, 240, S13_COLOR_PANEL);
    s13_video_draw_box(60, 120, 1800, 240, 2, S13_COLOR_MUTED);

    s13_video_draw_text(90, 150, "GAME INSTALLATION & RUNTIME STATUS:", S13_COLOR_TEXT);
    uint32_t status_color = (ui->game_info.status == GAME_STATUS_READY) ? S13_COLOR_SUCCESS : S13_COLOR_WARNING;
    s13_video_draw_text(450, 150, ui->game_info.status_message, status_color);

    char buf[256];
    snprintf(buf, sizeof(buf), "Executable : %s", ui->game_info.exe_path);
    s13_video_draw_text(90, 190, buf, S13_COLOR_MUTED);

    snprintf(buf, sizeof(buf), "Wine Prefix: %s", ui->game_info.prefix_path);
    s13_video_draw_text(90, 220, buf, S13_COLOR_MUTED);

    snprintf(buf, sizeof(buf), "Resolution : %dx%d (%s, VSync)", ui->settings.width, ui->settings.height,
             s_qualities[ui->settings.quality > 2 ? 1 : ui->settings.quality]);
    s13_video_draw_text(90, 250, buf, S13_COLOR_MUTED);

    snprintf(buf, sizeof(buf), "Mods Found : %s", ui->game_info.has_mods ? "Kitserver13 / Community Patch Active" : "None (Clean)");
    s13_video_draw_text(90, 280, buf, ui->game_info.has_mods ? S13_COLOR_SUCCESS : S13_COLOR_MUTED);

    // Notice banner
    if (ui->notice_message[0]) {
        s13_video_draw_text(90, 320, ui->notice_message, ui->notice_color);
    }

    // View content
    if (ui->current_view == VIEW_MAIN_MENU) {
        const char *menu_items[] = {
            "PLAY SOCCER13",
            "DISPLAY & GRAPHICS SETTINGS",
            "INSTALL / REPAIR GAME PREFIX",
            "BACKUP / RESTORE SAVE DATA",
            "ABOUT & HARDWARE SPECS"
        };

        for (int i = 0; i < 5; ++i) {
            int y = 400 + i * 80;
            bool selected = (ui->selected_item == i);
            uint32_t bg = selected ? S13_COLOR_ACCENT : S13_COLOR_PANEL;
            uint32_t text_col = selected ? S13_COLOR_TEXT : S13_COLOR_MUTED;

            s13_video_draw_rect(200, y, 1520, 60, bg);
            s13_video_draw_box(200, y, 1520, 60, 2, selected ? S13_COLOR_TEXT : S13_COLOR_MUTED);

            char label[64];
            snprintf(label, sizeof(label), "%s %s", selected ? "> " : "  ", menu_items[i]);
            s13_video_draw_text(240, y + 20, label, text_col);
        }

    } else if (ui->current_view == VIEW_SETTINGS) {
        s13_video_draw_rect(200, 400, 1520, 400, S13_COLOR_PANEL);
        s13_video_draw_box(200, 400, 1520, 400, 2, S13_COLOR_ACCENT);

        s13_video_draw_text(240, 430, "DISPLAY & GRAPHICS CONFIGURATION (WRITES SETTINGS.DAT):", S13_COLOR_TEXT);

        int res_idx = (ui->settings.width == 1920) ? 2 : (ui->settings.width == 1600 ? 1 : 0);
        snprintf(buf, sizeof(buf), "%s Resolution       : < %s >", (ui->selected_item == 0) ? ">" : " ", s_resolutions[res_idx]);
        s13_video_draw_text(240, 490, buf, (ui->selected_item == 0) ? S13_COLOR_ACCENT : S13_COLOR_TEXT);

        snprintf(buf, sizeof(buf), "%s Graphics Quality : < %s >", (ui->selected_item == 1) ? ">" : " ", s_qualities[ui->settings.quality % 3]);
        s13_video_draw_text(240, 540, buf, (ui->selected_item == 1) ? S13_COLOR_ACCENT : S13_COLOR_TEXT);

        snprintf(buf, sizeof(buf), "%s Display Mode     : < %s >", (ui->selected_item == 2) ? ">" : " ", ui->settings.fullscreen ? "Fullscreen" : "Windowed");
        s13_video_draw_text(240, 590, buf, (ui->selected_item == 2) ? S13_COLOR_ACCENT : S13_COLOR_TEXT);

        snprintf(buf, sizeof(buf), "%s [ SAVE SETTINGS & RETURN ]", (ui->selected_item == 3) ? ">" : " ");
        s13_video_draw_text(240, 660, buf, (ui->selected_item == 3) ? S13_COLOR_SUCCESS : S13_COLOR_MUTED);

    } else if (ui->current_view == VIEW_ABOUT) {
        s13_video_draw_rect(200, 400, 1520, 400, S13_COLOR_PANEL);
        s13_video_draw_box(200, 400, 1520, 400, 2, S13_COLOR_MUTED);

        s13_video_draw_text(240, 440, "SOCCER13 (PC -> PS4 HEN Compatibility Port)", S13_COLOR_TEXT);
        s13_video_draw_text(240, 480, "Base Runtime: orbis-win (ABI-v4) by plastikman", S13_COLOR_MUTED);
        s13_video_draw_text(240, 510, "Reference   : futbol13 by 7tg", S13_COLOR_MUTED);
        s13_video_draw_text(240, 540, "DXVK        : 2.6.2 (Direct3D 9 -> Vulkan RADV)", S13_COLOR_MUTED);
        s13_video_draw_text(240, 570, "Wine        : Native WoW64 (i386 PE32 via 56KB Relocation Stub)", S13_COLOR_MUTED);
        s13_video_draw_text(240, 600, "Clean-Room  : 100% Free of copyrighted logos or proprietary binaries", S13_COLOR_SUCCESS);

    } else if (ui->current_view == VIEW_INSTALL_REPAIR) {
        s13_video_draw_rect(200, 400, 1520, 400, S13_COLOR_PANEL);
        s13_video_draw_box(200, 400, 1520, 400, 2, S13_COLOR_MUTED);
        s13_video_draw_text(240, 440, "INSTALL & REPAIR ENGINE", S13_COLOR_TEXT);
        s13_video_draw_text(240, 480, "- Automatically copies game & mod folders (kitserver13)", S13_COLOR_MUTED);
        s13_video_draw_text(240, 510, "- Injects Windows Registry for CPU and VRAM check bypass", S13_COLOR_MUTED);
        s13_video_draw_text(240, 540, "- Generates verified 852-byte settings.dat", S13_COLOR_MUTED);
        s13_video_draw_text(240, 570, "- Save protection: Never overwrites EDIT.bin or career data!", S13_COLOR_SUCCESS);
        s13_video_draw_text(240, 620, "Press [Circle] to return to Main Menu", S13_COLOR_MUTED);

    } else if (ui->current_view == VIEW_SAVE_BACKUP) {
        s13_video_draw_rect(200, 400, 1520, 400, S13_COLOR_PANEL);
        s13_video_draw_box(200, 400, 1520, 400, 2, S13_COLOR_MUTED);
        s13_video_draw_text(240, 440, "SAVE DATA MANAGEMENT", S13_COLOR_TEXT);
        s13_video_draw_text(240, 480, "Path: drive_c/users/prospero/Documents/KONAMI/Pro Evolution Soccer 2013/save/", S13_COLOR_MUTED);
        s13_video_draw_text(240, 520, "Contains: EDIT.bin (Squads/Transfers), OPTION.bin, Master League Saves", S13_COLOR_MUTED);
        s13_video_draw_text(240, 560, "Status: Safe & Protected from Repair operations.", S13_COLOR_SUCCESS);
        s13_video_draw_text(240, 620, "Press [Circle] to return to Main Menu", S13_COLOR_MUTED);

    } else if (ui->current_view == VIEW_LOG_VIEWER) {
        s13_video_draw_rect(200, 400, 1520, 400, S13_COLOR_PANEL);
        s13_video_draw_box(200, 400, 1520, 400, 2, S13_COLOR_MUTED);
        s13_video_draw_text(240, 440, "RUNTIME LOG VIEWER", S13_COLOR_TEXT);
        s13_video_draw_text(240, 480, "Active Log: /data/prospero-win/logs/session-0.log", S13_COLOR_MUTED);
        s13_video_draw_text(240, 520, "Diagnostic Server: ps5logd (port 9300)", S13_COLOR_MUTED);
        s13_video_draw_text(240, 560, "Retrieve logs to PC anytime via: ./scripts/deploy-ps4.sh fetch-logs", S13_COLOR_ACCENT);
        s13_video_draw_text(240, 620, "Press [Circle] to return to Main Menu", S13_COLOR_MUTED);
    }

    // Footer bar
    s13_video_draw_rect(0, 1020, S13_SCREEN_WIDTH, 60, S13_COLOR_HEADER);
    s13_video_draw_text(60, 1040, "[D-Pad] Navigate   [Cross] Select/Confirm   [Circle] Back/Exit   [Triangle] View Logs", S13_COLOR_TEXT);

    // Present / Flip
    s13_video_flip();
}
