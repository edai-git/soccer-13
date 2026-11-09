#pragma once

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// SOCCER13 Button Bitmask mappings (libScePad compatible)
#define S13_PAD_L3        (1u << 1)
#define S13_PAD_R3        (1u << 2)
#define S13_PAD_OPTIONS   (1u << 3)
#define S13_PAD_UP        (1u << 4)
#define S13_PAD_RIGHT     (1u << 5)
#define S13_PAD_DOWN      (1u << 6)
#define S13_PAD_LEFT      (1u << 7)
#define S13_PAD_L2        (1u << 8)
#define S13_PAD_R2        (1u << 9)
#define S13_PAD_L1        (1u << 10)
#define S13_PAD_R1        (1u << 11)
#define S13_PAD_TRIANGLE  (1u << 12)
#define S13_PAD_CIRCLE    (1u << 13)
#define S13_PAD_CROSS     (1u << 14)
#define S13_PAD_SQUARE    (1u << 15)
#define S13_PAD_TOUCHPAD  (1u << 20)

typedef struct {
    uint32_t buttons_down;     // Currently held down
    uint32_t buttons_pressed;  // Just pressed this frame (edge-triggered)
    uint32_t buttons_released; // Just released this frame
    int16_t left_stick_x;
    int16_t left_stick_y;
    int16_t right_stick_x;
    int16_t right_stick_y;
    bool connected;
} s13_input_state_t;

bool s13_input_init(void);
void s13_input_poll(s13_input_state_t *state);
void s13_input_shutdown(void);

#ifdef __cplusplus
}
#endif
