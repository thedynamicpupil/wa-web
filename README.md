# Armageddon Recomp

Static x86 binary recompilation of **Worms Armageddon (`WA.exe`)** to **WebAssembly + WebGPU** (with a native headless verification harness) using [`veritr1x/recomp-kit`](https://github.com/veritr1x/recomp-kit).

> **Legal Notice:** This repository contains **zero** copyrighted *Worms Armageddon* binaries, assets, or lifted code. Users supply their own legally owned DRM-free **GOG.com** *Worms Armageddon* v3.8.1 installation in the git-ignored `game/WA_GOG/` (symlinked to `original/`) directory.

---

## Current Status

- **Static Recompilation:** Full `WA.exe` (GOG v3.8.1, `SHA-256: 10d8172b5761bb5a1cb4ec219fdaca5015c0b86b6638c8dbcc8f5d0618c0a8b9`) translated — **13,359 / 13,360 functions**, **537 / 537 jump tables**, **0 recovery errors**, **0 undeliverable calls**.
- **WebAssembly + WebGPU Build:** Boots cleanly in browser (`ArmageddonRecomp.wasm`), streams GOG assets from OPFS, plays the Team17 & Worms Armageddon intro sequence, and enters the full animated **Main Menu** at `640×480×32bpp`.
- See [STATUS.md](STATUS.md) for detailed progress, shim inventory, and next session TODOs.

---

## Architecture

- **`kit/`** — [`veritr1x/recomp-kit`](https://github.com/veritr1x/recomp-kit) git submodule providing x86-to-C translation (`tools/`), guest x86 runtime & Win32/MFC shims (`runtime/`), DirectDraw / DirectSound / DirectInput shims (`dx/`), SDL3 host (`host/`), and WebAssembly launcher/player (`web/`).
- **`game.toml` & `globals.toml`** — Identity, PE addresses (`image_base = 0x00400000`, `entry_point = 0x005d8b6c`), translator settings, and curated symbols for `WA.exe`.
- **`game/` & `original/`** *(git-ignored)* — User's local DRM-free GOG *Worms Armageddon* installation.
- **`analysis/` & `build/`** *(git-ignored)* — Ghidra disassembly listings, translated C output, and compiled headless / WebAssembly targets.

---

## Quick Start (Build & Run Web Version)

### Prerequisites
- **Ghidra 12.1.3** + **OpenJDK 21** (headless disassembly export)
- **CMake**, **Ninja**, **Clang**, **Python 3** (`.venv`)
- **Emscripten** (`emcc`) for WebAssembly builds

### First-Time Setup
```bash
git clone --recurse-submodules https://github.com/dogukanduran/wa-web && cd wa-web
python3 -m venv .venv && .venv/bin/pip install -r kit/requirements-dev.txt
.venv/bin/python kit/tools/setup.py --game-dir "$PWD" --install "/path/to/Worms Armageddon" --link-only
GHIDRA_HOME=/path/to/ghidra_12.1.3_PUBLIC tools/export_listings.sh
.venv/bin/python tools/build.py --target headless --regenerate
```
Full details are in [CONTRIBUTING.md](CONTRIBUTING.md).

### Build WebAssembly & Serve
```bash
# 1. Activate Emscripten, build WebAssembly and stage the WA-only site
source /path/to/emsdk/emsdk_env.sh
.venv/bin/python tools/build.py --target web --jobs 3

# 2. Stage WA-only Play site and serve on http://localhost:8080/
.venv/bin/python tools/serve_web.py --serve 8080
```

The build uses the kit driver and then stages this repository's WA-only player.
Existing `assets.pak` is reused; use `tools/serve_web.py --repack` after changing
the private installation. Add `--regenerate` to the build command when translation
inputs change. The build needs prepared game inputs as described above.

### Headless Verification (Native macOS)
```bash
cmake --build build/cmake/macos --target pop_headless --parallel 8
rm -f /tmp/wa_clean_reg.json
RECOMP_REGISTRY=/tmp/wa_clean_reg.json ./build/recomp/pop_headless
```

---

## Contributing

Contributions are welcome: missing Win32/DirectX shims, rendering and audio fixes, getting into matches, browser polish. Read [CONTRIBUTING.md](CONTRIBUTING.md) first, especially the rules on game files, and see the open TODOs in [STATUS.md](STATUS.md#4-next-session-todos-known-issues-to-investigate--fix).

## License

The handwritten files in this repository are [MIT-licensed](LICENSE). `kit/` carries its own license. Worms Armageddon and all of its content belong to their owners; see [NOTICE](NOTICE).
