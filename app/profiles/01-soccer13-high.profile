; 01-soccer13-high.profile — SOCCER 13 High Preset (1080p Full HD)
[application]
id = 01-soccer13-high
name = 1. HIGH 1080p (Rata-Kanan)
executable = D:\pes2013.exe
working_directory = D:\
dll_overrides = d3d8,d3d9,d3d10core,d3d11,dxgi=n;dinput8=n,b
prefix = soccer13
runtime = wine-wow64
architecture = pe32
graphics = dxvk

[display]
desktop = 1920x1080
scaling = fit
show_fps = false

[input]
mode = xinput
options = escape
mouse = touchpad
mouse_speed = 400
touchpad = mouse_left

[runtime]
cpu = native
thread_scheduling = true

[debug]
winedebug = -all
env = PW_PS4_FORCE_EXEC=0
env = PW_WINESERVER_HEAP_DIRECT=1

