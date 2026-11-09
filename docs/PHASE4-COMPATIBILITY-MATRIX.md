# PHASE4-COMPATIBILITY-MATRIX.md — SOCCER13 Hardware Compatibility Matrix & Diagnostics

**Project:** `soccer13` (SOCCER13 PC → PS4 HEN)  
**Standard Compliance:** [AGENTS.md](file:///d:/dev/DEV/other/ps4/soccer13/AGENTS.md) §6.5 (Section 9.2 Hardware Testing Standard)

---

## 1. 12-Stage Execution Protocol Matrix

The compatibility of `SOCCER13` on target PlayStation 4 hardware is evaluated through 12 discrete, reproducible stages:

| # | Execution Stage | Verification Target | Expected Log / Console Indicator | Status |
|---|---|---|---|---|
| **1** | **Wine Startup** | Orbis OS relocation stub handoff to PRX | `PW_WINE64 build_marker=...`<br>`PW_WINE64 relocatable eboot release status=0` | READY |
| **2** | **Game Process Startup** | PE32 32-bit executable invocation | `ImageBase=0x400000`, `wow64native.dll` mapped | READY |
| **3** | **Game Initialization** | Startup registry & settings read | Registry `installdir` & `~MHz` read, `settings.dat` 852B loaded | READY |
| **4** | **Main Menu** | Direct3D 9 -> Vulkan surface active | `win32u: headless surface: res 0`<br>`wsi/orbis: swapchain scaled to 1920x1080` | READY |
| **5** | **Team Selection** | 2D/3D interface navigation via DualShock 4 | `xinput1_3.prx` pad read events active, D-Pad responsive | READY |
| **6** | **Match Loading** | Shader compilation & stadium asset unpack | `d3d9.numCompilerThreads = 2`, `img/` archives read | READY |
| **7** | **Gameplay Rendering** | In-game pitch, 22 players, ball physics | 60 FPS target at 1280x720 / 1600x900, stable frame pacing | READY |
| **8** | **Audio Subsystem** | Sound effects & commentary playback | `wineps5.prx` audio stream buffer active, no underrun | READY |
| **9** | **Controller Input** | DualShock 4 sticks, triggers, face buttons | Pass/Shoot/Sprint/Skill moves respond with low latency | READY |
| **10** | **Match Completion** | Full match (10+ min) without memory leak | VRAM stable, no `PW_ORBIS_VA_FAIL`, no OOM | READY |
| **11** | **Save / Load** | Write/read of `EDIT.bin` & Master League | Prefix save path written, file size unchanged | READY |
| **12** | **Clean Exit** | In-game Quit or PS Home Button close | `guest processes ended: ...`, exit code `0` | READY |

---

## 2. Edition Compatibility & Mod Support Matrix

| Edition / Mod Configuration | Validation Criteria | Prefix Staging Rule | Recommended Settings |
|---|---|---|---|
| **Retail (with `code.txt`)** | `pes2013.exe` (PE32) + `img/` + valid 20-char key | Registry receives user serial from `code.txt` | 1280x720 Medium, VSync On |
| **Repack / Pre-Cracked** | `pes2013.exe` (PE32) + `img/` (no `code.txt`) | Registry automatically receives default fallback key | 1280x720 Medium, VSync On |
| **Community Mod (Kitserver13)** | `pes2013.exe` + `kitserver13/` + `kload.dll` | `kitserver13/` copied intact; `dll_overrides = ...;dinput8=n,b` | 1280x720 Medium, VSync On |
| **Updated Squads (`EDIT.bin`)** | User supplied `save/EDIT.bin` in source | Staged to user Documents; protected from Repair | Compatible with all editions |

---

## 3. Hardware Model Tuning Guide

### PS4 Fat / Slim (1.6 GHz Jaguar, 1.84 TFLOPS GCN)
- **Baseline Resolution:** `1280x720` (720p)
- **Quality:** `Medium`
- **DXVK Compiler Threads:** `dxvk.numCompilerThreads = 2` (prevents Jaguar thread starvation)
- **Framerate Target:** 60 FPS

### PS4 Pro (2.13 GHz Jaguar, 4.2 TFLOPS GCN, NEO Mode)
- **Baseline Resolution:** `1600x900` or `1920x1080` (1080p)
- **Quality:** `High`
- **NEO Flag:** Supports packaging with `--neo` flag
- **Framerate Target:** Solid 60 FPS

---

## 4. Automated Log Analysis Standard

After running on console, fetch logs and run the automated analyzer:
```bash
./scripts/deploy-ps4.sh fetch-logs artifacts/logs/
./scripts/deploy-ps4.sh analyze-logs artifacts/logs/session-0.log
```
The analyzer (`scripts/analyze-session-log.py`) will output a stage-by-stage PASS/FAIL breakdown and isolate any guest faults.

