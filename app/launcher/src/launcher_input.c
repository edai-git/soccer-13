#include "launcher_input.h"
#include <string.h>

static s13_input_state_t s_prev_state;

bool s13_input_init(void) {
    memset(&s_prev_state, 0, sizeof(s_prev_state));
    // In native PS4 execution, this calls scePadInit() and scePadOpen(userId, 0, 0, NULL)
    return true;
}

void s13_input_poll(s13_input_state_t *state) {
    if (!state) return;

    // Edge triggering: pressed = (current & ~previous), released = (~current & previous)
    state->buttons_pressed = state->buttons_down & ~s_prev_state.buttons_down;
    state->buttons_released = ~state->buttons_down & s_prev_state.buttons_down;

    s_prev_state = *state;
}

void s13_input_shutdown(void) {
    // In native PS4 execution, calls scePadClose()
    memset(&s_prev_state, 0, sizeof(s_prev_state));
}

