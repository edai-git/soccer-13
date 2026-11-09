; SOCCER13 profile for orbis-win (PS4 HEN)
; 32-bit Direct3D 9 via DXVK 2.6.2 on Native WoW64

[application]
id = soccer13
name = SOCCER13
executable = C:\Games\SOCCER13\pes2013.exe
working_directory = C:\Games\SOCCER13
dll_overrides = d3d8,d3d9,d3d10core,d3d11,dxgi=n;dinput8=n,b
prefix = soccer13
runtime = wine-wow64
architecture = pe32
graphics = dxvk

[display]
desktop = 1280x720

[input]
mode = xinput
options = escape
mouse = touchpad
mouse_speed = 400
touchpad = mouse_left

[runtime]
cpu = native

[debug]
env = PW_WINESERVER_HEAP_DIRECT=1;PW_PS4_FORCE_EXEC=0

