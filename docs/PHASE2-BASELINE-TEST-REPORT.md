# Phase 2: Baseline Runtime Hardware Test Report & Runbook

**Project:** `soccer13` (SOCCER13 PC → PS4 HEN)  
**Milestone:** Phase 2: Baseline Runtime Verification  
**Standard Compliance:** [AGENTS.md](file:///d:/dev/DEV/other/ps4/soccer13/AGENTS.md) §6.5 (Section 9.2 Hardware Testing Standard)

---

## 1. Overview & Objective

Phase 2 establishes and proves that the [`plastikman/orbis-win`](https://github.com/plastikman/orbis-win) (ABI-v4) baseline runtime:
1. Builds cleanly into a valid relocatable PlayStation 4 package (`.pkg`) with the 56 KB no-RELRO relocation stub `eboot.bin` and high-address `sce_module/relocated_wine_app.prx`.
2. Packages OpenOrbis clean-room stubs (`libc.prx`, `libSceFios2.prx`) without proprietary Sony console binaries.
3. Passes all 8 hard gates in `check-ps4-package-parity.py` and `PkgTool.Core pkg_validate`.
4. Successfully boots on target PS4 HEN hardware, initialises Wine in `/data/prospero-win/prefixes/`, maps the controller, presents video frames via RADV, and achieves verified gameplay with a reference Windows game (e.g. *Space Cadet Pinball* `pinball` or *Half-Life 2* `half-life-2`).

> [!IMPORTANT]
> **Hardware Truth Only (AGENTS.md Rule 17):** Never mark Phase 2 as complete or claim gameplay success solely because the Docker container built the PKG. Hardware verification requires actual installation and log collection on target PS4 hardware running GoldHEN.

---

## 2. Test Environment Metadata Template

When executing tests on the physical console, fill out the following mandatory metadata block:

```text
================================================================================
                    PS4 HARDWARE RUNTIME TEST METADATA
================================================================================
Test Date & Time (UTC)   : [YYYY-MM-DD HH:MM:SS]
Tester / Operator        : [Name / Handle]
PS4 Console Model        : [Fat (CUH-10xx/11xx/12xx) / Slim (CUH-20xx/21xx/22xx) / Pro (CUH-70xx/71xx/72xx)]
System Firmware Version  : [e.g. 9.00 / 11.00]
HEN / GoldHEN Version    : [e.g. GoldHEN v2.4b16.2]
Package Filename         : [e.g. ORBIS-WIN-BASELINE.pkg / SOCCER13-PS4.pkg]
Package SHA-256 Checksum : [64-char hex string from sha256sum]
Title ID / APP_VER       : [e.g. GLDS10043 / 01.49]
Git Commit SHA (soccer13): [Commit hash]
Git Commit SHA (orbis-win): 9d762029157acc94686b2ac76d48ac383938a4fb (ABI-v4)
Reference Game Tested    : [Space Cadet Pinball (pinball) / Half-Life 2 (half-life-2)]
================================================================================
```

---

## 3. 12-Stage Hardware Test Protocol

Record `PASS` or `FAIL` with observations for every stage:

| Stage # | Stage Name | Verification Criteria | Expected Hardware Behavior | Result (PASS/FAIL) | Notes / Error Message |
|:---:|---|---|---|:---:|---|
| **1** | **Package Installation** | PKG installs via GoldHEN Package Installer without error `CE-34878-0` or `0x80020002`. | Console home screen displays tile with Title ID and valid icon. | `[PENDING]` | |
| **2** | **EBOOT Handoff** | 56 KB no-RELRO relocation stub executes at `0x55c000`. | Does not crash at launch; transitions immediately to loading the app PRX. | `[PENDING]` | |
| **3** | **App PRX Initialization** | `relocated_wine_app.prx` loads at high address; releases `eboot.bin` mapping. | Log records `PW_WINE64 relocatable eboot release status=0`. | `[PENDING]` | |
| **4** | **Wine Prefix Setup** | Wine runtime creates `/data/prospero-win/prefixes/<title>/` structure. | `drive_c`, `system.reg`, `user.reg` populated; no permissions error on `/data`. | `[PENDING]` | |
| **5** | **Process Execution** | Selected PE32 Windows executable is invoked. | PE header validated; `0x400000` image base is free and mapped without collision. | `[PENDING]` | |
| **6** | **Graphics Presentation** | Direct3D 9 / Vulkan surface initialization via RADV. | Display output active; no black screen, hang, or GPU page fault in klog. | `[PENDING]` | |
| **7** | **Audio Subsystem** | DirectSound audio stream via `wineps5.prx` and `libSceAudioOut`. | In-game sound effects and background music play clearly without buffer stutter. | `[PENDING]` | |
| **8** | **Input Mapping** | DualShock 4 controller input translated via `xinput1_3.prx` / `libScePad`. | D-Pad, face buttons (Cross/Circle), and analogs respond in menu and gameplay. | `[PENDING]` | |
| **9** | **In-Game Navigation** | Player enters menu, starts a match/round, and renders active gameplay. | 3D graphics rendered at stable frame pacing without freeze or memory leak. | `[PENDING]` | |
| **10** | **Gameplay Session** | Continuous gameplay for at least 5 minutes. | No memory exhaustion, no uncaught C0000005 exception in `session-0.log`. | `[PENDING]` | |
| **11** | **Clean Exit** | Exit game via in-game menu or PS Home button. | Process terminates cleanly; returns to launcher or PS4 Home without kernel crash. | `[PENDING]` | |
| **12** | **Log Retrieval** | Session logs and crash diagnostics extracted. | `/data/prospero-win/logs/session-0.log` retrieved via FTP or ps5logd. | `[PENDING]` | |

---

## 4. Console Execution Runbook

### Step 1: Configure Network (NFR-05 Compliant)
Create a `.env` file in the project root on the build host (never committed to git):
```ini
PS4_HOST=192.168.1.50
PS4_FTP_PORT=2121
PS4_LOG_PORT=9300
```

Verify connection:
```bash
./scripts/deploy-ps4.sh status
```

### Step 2: Install Package on PS4
1. Copy `artifacts/baseline/ORBIS-WIN-BASELINE.pkg` to a FAT32/exFAT USB root, or install via GoldHEN FTP / Package Installer.
2. Launch GoldHEN on the PS4, open **Package Installer**, and install the package.

### Step 3: Deploy Reference Game Profile & Files
For Space Cadet Pinball:
```bash
./scripts/deploy-ps4.sh push-profile runtime/orbis-win/src/profiles/pinball.profile
```

### Step 4: Run Live Logging (Optional, Recommended)
In a separate terminal on your development PC:
```bash
./scripts/deploy-ps4.sh listen-logs
```

### Step 5: Launch Title on PS4
1. Press Cross on the installed homebrew tile.
2. Observe screen transition, launch of reference title, input response, and audio.
3. Complete at least 5 minutes of gameplay.
4. Exit via game menu or PS button.

### Step 6: Fetch Session Logs
```bash
./scripts/deploy-ps4.sh fetch-logs artifacts/logs/
```

Check the log contents:
```bash
cat artifacts/logs/session-0.log
```

Key lines to look for:
- `PW_WINE64 build_marker=...`
- `PW_WINE64 relocatable eboot release status=0`
- `guest processes ended: ...`

---

## 5. Hardware Test Sign-off Checklist

- [ ] Metadata recorded accurately (Console model, FW, GoldHEN version).
- [ ] No kernel panic or PS4 OS system crash during installation or execution.
- [ ] Session log `session-0.log` saved and archived in `artifacts/logs/`.
- [ ] Reference game passed Stages 1 through 12.
- [ ] Phase 2 Hardware Gate Approved to proceed to Phase 3 (SOCCER13 Integration).
