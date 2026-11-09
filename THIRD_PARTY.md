# THIRD_PARTY.md — Third-Party Licenses & Attributions for SOCCER13

**Project:** `soccer13` / `SOCCER13`  
**Target Platform:** PlayStation 4 (PS4 HEN / GoldHEN)  
**Type:** Clean-Room Windows PC Game Compatibility Port & Launcher

---

## 1. Clean-Room & Non-Affiliation Declaration

`SOCCER13` is an independent, non-commercial open-source homebrew software project. 

- This repository and the distributed `.pkg` package contain **NO game executables (`.exe`), NO proprietary dynamic-link libraries (`.dll`), NO game assets (`.img`), NO save files, and NO trademarks, logos, or copyrighted audio/graphics** belonging to Konami Digital Entertainment Co., Ltd. or Sony Interactive Entertainment Inc.
- All game files and mod assets are supplied by the end-user from their legally acquired Windows PC installation.
- All package identity, UI assets, launcher code, and configuration scripts use the neutral name **`SOCCER13`** to avoid trademark infringement.

---

## 2. Open-Source Component Attributions

`SOCCER13` builds upon and integrates the following open-source projects and libraries:

### 2.1. orbis-win & prospero-win
- **Upstream Authors:** Zak Peirce (plastikman), mpereiraesaa, and contributors
- **Repositories:**
  - https://github.com/plastikman/orbis-win
  - https://github.com/plastikman/prospero-win
  - https://github.com/mpereiraesaa/prospero-win
- **Pinned Commit:** `9d762029157acc94686b2ac76d48ac383938a4fb` (ABI-v4 / v0.0.3)
- **License:** GNU Lesser General Public License v2.1 or later (LGPL-2.1-or-later)

### 2.2. Wine (Wine Is Not an Emulator)
- **Authors:** The Wine project contributors
- **Repository:** https://gitlab.winehq.org/wine/wine
- **Pinned Commit:** `490f6d5dcbb2a5047345b8af88d114bbcaad69a8`
- **License:** GNU Lesser General Public License v2.1 or later (LGPL-2.1-or-later)

### 2.3. Mesa / RADV PS4
- **Authors:** The Mesa 3D Graphics Library authors & orbis-ports contributors
- **Repository:** https://github.com/orbis-ports/mesa-ps4
- **Pinned Commit:** `1a59cc1` (with PS4 patches 0001–0044)
- **License:** MIT License

### 2.4. DXVK (Direct3D 9 to Vulkan Translation Layer)
- **Author:** Philip Rebohle (doitsujin) and contributors
- **Repository:** https://github.com/doitsujin/dxvk
- **Pinned Version:** `2.6.2` (SHA-256: `8011c25caeb1f0a4f5f5407dc7ddfe5ef9d7d42cfb2d07ae68e82a7f5a8bf129`)
- **License:** zlib/libpng License

### 2.5. OpenOrbis PS4 Toolchain & Module Stubs
- **Authors:** OpenOrbis Team & contributors
- **Repository:** https://github.com/OpenOrbis/OpenOrbis-PS4-Toolchain
- **Pinned Commit:** `0a1aaf9dd4a92695538bdeb09fb056d06dd11725`
- **Component:** Clean-room module stubs (`libc.prx`, `libSceFios2.prx` under `src/openorbis-module-stubs/`)
- **License:** GNU General Public License v3.0 (GPL-3.0)

### 2.6. FreeType
- **Authors:** David Turner, Robert Wilhelm, Werner Lemberg, and contributors
- **Website:** https://www.freetype.org
- **Pinned Version:** `2.13.3` (SHA-256: `0550350666d427c74daeb85d5ac7bb353acba5f76956395995311a9c6f063289`)
- **License:** The FreeType Project LICENSE (FTL) / GNU General Public License v2.0 (GPL-2.0)

### 2.7. Reference Implementation: futbol13
- **Author:** 7tg (https://github.com/7tg/futbol13)
- **Notice:** Provided architectural insights for neutral branding, settings.dat binary layout, and non-destructive installation workflows.

---

## 3. Licenses Text Summary

### LGPL-2.1 Summary
This library is free software; you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation; either version 2.1 of the License, or (at your option) any later version.

### MIT License Summary
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so.

### zlib/libpng License Summary
This software is provided 'as-is', without any express or implied warranty. In no event will the authors be held liable for any damages arising from the use of this software. Permission is granted to anyone to use this software for any purpose, including commercial applications, and to alter it and redistribute it freely.

