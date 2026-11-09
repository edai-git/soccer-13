#include "launcher_ui.h"
#include "launcher_video.h"
#include "launcher_input.h"
#include <stdio.h>
#include <unistd.h>

int main(int argc, char **argv) {
    (void)argc;
    (void)argv;

    // 1. Initialize VideoOut
    if (!s13_video_init()) {
        fprintf(stderr, "[-] Failed to initialize SOCCER13 VideoOut\n");
        return 1;
    }

    // 2. Initialize Input (DualShock 4)
    if (!s13_input_init()) {
        fprintf(stderr, "[-] Failed to initialize SOCCER13 Input\n");
        s13_video_shutdown();
        return 1;
    }

    // 3. Initialize UI state
    s13_ui_state_t ui;
    s13_ui_init(&ui);

    s13_input_state_t input;
    memset(&input, 0, sizeof(input));

    // 4. Main Event Loop
    while (!ui.should_exit) {
        // Poll DualShock 4
        s13_input_poll(&input);

        // Update UI state machine
        s13_ui_update(&ui, &input);

        // Render Frame
        s13_ui_render(&ui);

        // Cap frame rate (~60 FPS)
        usleep(16666);
    }

    // 5. Cleanup
    s13_input_shutdown();
    s13_video_shutdown();
    return 0;
}

