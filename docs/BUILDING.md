# Building SOCCER13 for PS4 HEN

This document provides complete instructions for building the **SOCCER13** PS4 compatibility package (`SOCCER13-PS4.pkg`).

The build system is **100% containerized with Docker** to guarantee reproducibility across development workstations.

---

## 1. Host Requirements

The host machine only requires:
- **Operating System:** Linux x86-64 or Windows 10/11 with **WSL2**
- **Docker:** Docker Engine 24+ and Docker Compose v2+
- **Git:** Git 2.30+
- **Disk Space:** ~20 GB free space for Docker build cache and intermediate Wine/RADV compilation

No compilers (Clang 19, MinGW), SDKs (OpenOrbis), or Wine dependencies need to be installed on your host machine.

---

## 2. Quick Start: Docker Build Pipeline

### Step 1: Clone Repository & Submodule
```bash
git clone --recurse-submodules https://github.com/your-org/soccer13.git
cd soccer13
```
If you cloned without `--recurse-submodules`:
```bash
git submodule update --init --recursive
```

### Step 2: Build the Docker Builder Image
```bash
docker compose build
```
This builds an Ubuntu 24.04 container image pinned to snapshot `20261012T000000Z` with **LLVM/Clang 19.1.7**, MinGW-w64, isolated OpenSSL 1.1, and all necessary build tools.

### Step 3: Run the Host Test Suite
```bash
docker compose run --rm builder test
```
Runs:
1. Lockfile and toolchain verification.
2. `settings.dat` 852-byte binary generator and CRC-16/XMODEM bitwise NOT checksum test.
3. Profile parser tests (`soccer13.profile`).
4. Clean-room repository audit (ensuring no proprietary game binaries or dumps are present).

### Step 4: Build Complete Package & Release Deliverables
```bash
docker compose run --rm builder release
```
Outputs in `release/`:
```text
release/
├── SOCCER13-PS4.pkg       # Installable PS4 homebrew package (GoldHEN)
├── BUILD-MANIFEST.txt     # Git commits, timestamps, and build provenance
├── SHA256SUMS             # SHA-256 hashes of all emitted release files
└── THIRD_PARTY.md         # Open-source license attributions
```

### Step 5: Clean Build Artifacts
```bash
docker compose run --rm builder clean
```

---

## 3. Build Architecture & Caching

The Docker pipeline uses a persistent named volume: `soccer13-build-cache` mounted at `/cache`:
- **OpenOrbis SDK Bundle:** Downloaded via `runtime/orbis-win/scripts/fetch-sdk.sh` and verified against SHA-256.
- **OpenOrbis Module Stubs:** Built from tracked GPL-3.0 source (`libc.prx` and `libSceFios2.prx`) without requiring Sony firmware blobs.
- **Relocatable Package Pipeline:** Assembles the 56 KB no-RELRO `eboot.bin` stub so the base address `0x400000` remains clear for the 32-bit PE32 game executable.

---

## 4. Troubleshooting

### Docker daemon connection error
If you see `failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine`:
- Make sure Docker Desktop is running on Windows and WSL2 integration is enabled under **Settings > Resources > WSL Integration**.

### `runtime/orbis-win` missing
Run `git submodule update --init --recursive` to pull the `orbis-win` submodule.

