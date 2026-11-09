cmake_minimum_required(VERSION 3.16)
project(soccer13_launcher C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

include_directories(include)

add_definitions(-D_GNU_SOURCE)
add_compile_options(-Wall -Wextra -O2)

set(LAUNCHER_SOURCES
    src/main.c
    src/launcher_ui.c
    src/launcher_video.c
    src/launcher_input.c
    src/launcher_game.c
    src/launcher_settings.c
    src/launcher_install.c
)

add_executable(soccer13_launcher ${LAUNCHER_SOURCES})

# If compiling with OpenOrbis / PS4 Clang toolchain, link Orbis libraries
if(DEFINED ENV{OO_PS4_TOOLCHAIN} OR DEFINED CMAKE_TOOLCHAIN_FILE)
    target_link_libraries(soccer13_launcher
        SceVideoOut
        ScePad
        SceUserService
        SceSystemService
    )
endif()

