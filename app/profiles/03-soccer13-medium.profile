; 03-soccer13-medium.profile — SOCCER 13 Medium Preset (720p 60FPS Recommended)
[application]
id = 03-soccer13-medium
name = 3. MEDIUM 720p (60 FPS Paling Stabil)
executable = C:\Games\SOCCER13\pes2013.exe
working_directory = C:\Games\SOCCER13
dll_overrides = d3d8,d3d9,d3d10core,d3d11,dxgi=n;dinput8=n,b
prefix = soccer13
runtime = wine-wow64
architecture = pe32
graphics = dxvk

[display]
desktop = 1280x720
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

