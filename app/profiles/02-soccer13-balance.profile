; 02-soccer13-balance.profile — SOCCER 13 Balance Preset (900p)
[application]
id = 02-soccer13-balance
name = 2. BALANCE 900p (Tajam di TV Standar)
executable = D:\pes2013.exe
working_directory = D:\
dll_overrides = d3d8,d3d9,d3d10core,d3d11,dxgi=n;dinput8=n,b
prefix = soccer13
runtime = wine-wow64
architecture = pe32
graphics = dxvk

[display]
desktop = 1600x900
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

