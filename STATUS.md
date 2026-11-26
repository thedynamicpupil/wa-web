# Armageddon Recomp — Session Handoff & Status

Last updated: 2026-11-26

## 2026-11-26: Asset-install buffer optimization

The WA-only asset worker now reads contiguous records directly from the download
chunk and assembles fragmented records in one allocation. Previously, each new
chunk reallocated and recopied the entire partial asset.

For a synthetic 8 MiB file delivered in 512 chunks of 16 KiB, instrumenting the
same worker before and after the change measured 2,151,677,952 bytes allocated
and copied before, versus 8,388,608 after (256.5 times less copying). These are
parser allocation/copy counts, not whole-browser memory or gameplay FPS.

Six Node tests cover contiguous and fragmented reads, retained views, empty
chunks/files, progress accounting, truncated downloads, reader errors and the
linear copy budget. Run `node tests/stream-buffer.test.cjs`; CI runs it too.
Headless Chrome 157 on Fedora successfully installed the fragmented 8 MiB
fixture, an empty file and a trailing text record into OPFS with exact bytes.
Reload reused the installation without requesting the pack again; no page
errors occurred. The real 146.7 MB pack also installed all 4,395 files; the
installed executable matched the configured SHA-256, and reload made no second
pack request. These checks validate installation, not game playback.

Fresh translation from the pinned kit `010cbcf` completed: 13,188 functions,
20,396 dispatch entries, no failures, unmodelled instructions, recovery errors
or jump-table gaps. The withdrawn candidate has data provenance. Real release
Wasm builds linked with Emscripten 7.0.1 and the documented 6.0.11 toolchain.
The first sandboxed translation was terminated; the successful retry ran outside
that sandbox. The final local build uses 6.0.11.

The kit driver then tried to stage a generic launcher removed from this kit
revision. `tools/build.py` now retains the normal kit build/lock flow and directs
its post-link staging callback to `tools/serve_web.py`, producing the WA-only
site and reusing its existing private asset pack. README commands use this path.

Headless Chrome 157 starts the guest and reports its 640x480 display mode and
audio generation, but the canvas GPU queue fails with an external-instance
error, followed by the presenter's completion timeout/device loss. The same
error reproduces with a plain JavaScript WebGPU canvas clear, without loading
Wasm or the recompiler; an empty GPU queue succeeds. The unchanged kit's browser readback/completion
fixture passes all 1,004 checks. No visible game frame,
sustained gameplay or FPS improvement is claimed. The local build is available
for hardware-browser review; gameplay optimization follows that review.
The kit submodule remains pinned and unchanged. An experimental instance-import
change did not resolve the game failure and is excluded from this PR.

The inherited milestones and pending gameplay checks below are historical.

---

## 1. Verified Working Milestones

- **Static Recompilation (`build/recomp/gen/`):**
  - `WA.exe` (GOG.com v3.8.1, `SHA-256: 10d8172b5761bb5a1cb4ec219fdaca5015c0b86b6638c8dbcc8f5d0618c0a8b9`)
  - **13,359 / 13,360 functions**, **20,412 entry points**, **537 / 537 jump tables (20,133 entries, 0 missing)**, **0 recovery errors**, **0 undeliverable calls**.
- **Runtime Boot & Rendering:**
  - Boots cleanly with **0 crashes** and **0 missing imports** in both `pop_headless` and WebAssembly (`ArmageddonRecomp.wasm`).
  - Sets `640×480×32bpp` DirectDraw display mode, loads all intro & Main Menu BMPs/PALs, fades the master palette (`0x008ac8c8`), renders the pixel-perfect **Team17** logo, **Worms Armageddon** title intro, and full animated **Main Menu** (falling stars + all menu buttons).
  - Clean exit via `WM_CLOSE` (`ExitProcess(0)`).
- **Web Launcher & Streaming:**
  - `build/web/recomp/ArmageddonRecomp.wasm` (33 MB) + `ArmageddonRecomp.js` (263 KB) built and staged with all **4,400 GOG assets (555 MB)** via `kit/tools/web_launcher.py --stream wa --serve 8080`.

---

## 2. Local Changes in `kit/` Submodule

All shims added/fixed in `kit/` during this session:
- **`kit/dx/ddraw.cpp` & `kit/runtime/gdi32.cpp` & `kit/host/present.cpp` & `kit/host/sdl/main.cpp`**:
  - Added 32-bit display modes (`640x480x32` .. `3840x2160x32`) to `kBuiltInModes`, enabled 32-bit `DDPIXELFORMAT` (`0x00ff0000` / `0x0000ff00` / `0x000000ff`) in `DD_EnumDisplayModes` and `DD_GetDisplayMode`, and allowed `ddraw_add_mode` / `host_display_offer_mode` to register 32bpp modes.
  - Wired `win32_display_mode` (`GetSystemMetrics(SM_CXSCREEN/SM_CYSCREEN)`) and `web_main` to detect and offer the host's actual screen / browser canvas resolution (`window.screen.width * devicePixelRatio`), so `WA.exe` defaults to and lists the player's native screen resolution under **Options → Graphics options** (`Custom Resolution`).
- **`kit/web/player/` & `kit/web/launcher/`**:
  - Added an interactive **Enter Fullscreen** suggestion banner (`Alt+Enter` / `F11`) to the web player and a fullscreen resolution tip to the launcher card.
- **`kit/runtime/kernel32.cpp` & `kernel32_wide.cpp`**:
  - Cleared `LastError` (`set_last_error(0)`) in `k_CreateSemaphoreA` so `WA.exe` doesn't think a second instance is running.
  - Added `GlobalAddAtomA`, `GlobalFindAtomA`, `GlobalGetAtomNameA`.
  - Added `Module32First` and `Module32Next` (2-arg `stdcall` shims returning `ERROR_NO_MORE_FILES`), preventing the `ESP` stack drift and null-call crash at `0x005306dd` when `WA.exe` inspects loaded modules at match startup (`0x0052e6d9`).
  - Added remaining `KERNEL32.dll` (`GetWindowsDirectoryA`, `LockFile`, `UnlockFile`, `MoveFileExA`, `ConvertDefaultLocale`, `GetPrivateProfileIntA`, `GetPrivateProfileStringA`, `WritePrivateProfileStringA`, `WriteProfileSectionA`, `FormatMessageA`, `lstrcmpW`, etc.), `GDI32.dll` (`CreatePen`, `SetPaletteEntries`, `OffsetViewportOrgEx`, `SetMapMode`, `SetWindowExtEx`, `SetViewportExtEx`, `ScaleWindowExtEx`, `ScaleViewportExtEx`, `PtVisible`, `Escape`, `ChoosePixelFormat`, `SetPixelFormat`, `SwapBuffers`), and `WSOCK32`/`WS2_32` (`ord5`/`getpeername`, `WSAAccept`) shims with exact `stdcall` argument counts.
- **`kit/runtime/misc.cpp`**:
  - Added ANSI registry functions: `RegSetValueA`, `RegQueryValueA`, `RegDeleteKeyA`, `RegDeleteValueA`, `RegEnumKeyA`, `RegEnumKeyExA`.
  - Implemented RIFF/WAV `WINMM.dll!mmioDescend` and `mmioAscend`.
- **`kit/runtime/gdi_image.h` & `kit/runtime/gdi32.cpp`**:
  - Added `gdi_create_dib_from_packed(...)` preserving native 8bpp/16bpp/24bpp/32bpp `DIBSECTION` format (required by `WA.exe` checking `dsBm.bmBitsPixel == 8`).
- **`kit/runtime/comctl32.cpp`**: Registered `InitCommonControlsEx` and `InitCommonControls`.
- **`kit/runtime/user32_wide.cpp`**: Registered `CallWindowProcA`.
- **`kit/runtime/user32_internal.h` & `kit/runtime/user32.cpp`**:
  - Implemented `WH_CBT` (`idHook == 5`) hook chain (`SetWindowsHookExA`, `UnhookWindowsHookEx`, `fire_cbt_createwnd`) so MFC's `_AfxCbtFilterHook` (`0x005c4c43`) attaches `CWnd::m_hWnd`.
  - Implemented `CreateDialogIndirectParamA` (parses `DLGTEMPLATE`/`DLGTEMPLATEEX` + child `DLGITEMTEMPLATE`/`DLGITEMTEMPLATEEX`, `6×13` MS Sans Serif base units, default `DefWindowProcA` wndproc, `window_created(chwnd)` for Z-order/`GW_CHILD`).
  - Changed `CreateWindowEx` / `CreateDialogIndirectParamA` geometry notifications from async `post_geometry` to synchronous `send_geometry` (`WM_SIZE`/`WM_MOVE`) so `CWnd::OnSize` (`fn_00425eb0`) doesn't wipe loaded BMP surfaces on the first message pump.
  - Fixed `SetWindowLongA(GWL_STYLE)` to sync `w->visible`/`w->enabled` and `ShowWindow` to dispatch `WM_SHOWWINDOW (0x0018)`.
  - Implemented `GetDlgItem`, `MapDialogRect`, `MoveWindow`, `LoadImageA` (file + resource + `LR_CREATEDIBSECTION`), `LoadBitmapA`, `SetWindowTextA`, `GetWindowTextA`, `GetWindowTextLengthA`, `SetDlgItemTextA`, `GetDlgItemTextA`, `SendDlgItemMessageA`, rect helpers (`PtInRect`, `CopyRect`, `OffsetRect`, `InflateRect`, `SetRectEmpty`, `EqualRect`, `SubtractRect`), plus ComboBox (`CB_*`), ListBox (`LB_*`), and Button (`BM_GETCHECK`, `BM_SETCHECK`, `BM_GETSTATE`, `BM_SETSTATE`, `BM_SETSTYLE`) message handling in `def_window_proc`.
  - Registered all built-in Win32 & common control window classes (`"button"`, `"edit"`, `"combobox"`, `"listbox"`, `"scrollbar"`, `"mdiclient"`, `"#32770"`, `"msctls_trackbar32"`, `"msctls_updown32"`, `"syslistview32"`, `"tooltips_class32"`, etc.) in `ensure_system_classes()` (`user32_static.cpp`), mapped `DLGITEMTEMPLATE` ordinal class atoms `#128`..`#133` to standard class names, and zeroed the output `RECT` on `GetWindowRect` failure so dynamically created dialog controls (e.g., Options -> **Advanced Options** dialog `0x22b` / `fn_00428bb0`) construct and render cleanly without crashing.
- **`kit/host/headless_main.cpp`**:
  - Added `RECOMP_CLICK_AT="frame:x:y,..."` environment variable support for deterministic multi-step UI click automation in `pop_headless`.
- **`kit/host/sdl/main.cpp`**:
  - Fixed `update_platform_pointer_capture()` to respect `host_cursor_visible()` so the OS cursor is not hidden on canvas click when `WA.exe` calls `ShowCursor(TRUE)`.
- **`kit/runtime/memory.cpp`**:
  - Expanded `RECOMP_WATCH` backtrace (`watch_writer()`) from 1 frame to 10 frames for faster debugging.

---

## 3. Verified `WA.exe` Key Addresses

- `0x005d8b6c`: PE entry point (`WinMainCRTStartup`)
- `0x005c4c43`: `_AfxCbtFilterHook` (MFC `WH_CBT` window creation hook)
- `0x0040bf60`: Root widget recursive painter
- `0x00403df0`: Sprite widget painter → `[0x79d6d4]->vtable[0x5c]` (`fn_005a2790` 8bpp software blitter)
- `0x00403b70`: Root frame presenter → `fn_0040d250` (cursor) → `fn_0059ed90` (Lock → `fn_005a1fa0` palette → `fn_005a2020` 8bpp→32bpp blit → Unlock → Flip)
- `0x0040ce20`: `SetCursor` GDI cursor builder (currently logs `gdi: REFUSED blit dst=00060006(-1x-1)` — see TODOs)
- `0x0040d250`: Cursor visibility & software cursor renderer (`[0x0088e3ec]` = hardware cursor flag)
- `0x00425eb0`: `CWnd::OnSize` handler
- `0x008ac8c8`: 256-entry master `PALETTEENTRY` array
- `0x007a0eec`: 640×480 8-bit software framebuffer pointer

---

## 4. Next Session TODOs (Known Issues to Investigate & Fix)

1. **Verify Browser Cursor & Text Fixes:**
   - Test `http://localhost:8080/` after the latest `ArmageddonRecomp.wasm` rebuild (OS cursor visibility + `GetWindowTextLengthA` / `SetWindowTextA` / `CB_*` / `LB_*` dropdowns).
   - If some button/dropdown texts are *still* missing:
     - Check whether `WA.exe` uses **`DrawTextA`**, **`DrawTextExA`**, **`TextOutA`**, or **`ExtTextOutA`** to paint owner-drawn controls/tooltips/dropdowns — currently `u_DrawTextA` (`user32.cpp:1935`) and `g_TextOutA` (`gdi32.cpp:712`) are no-op stubs, whereas `kit/runtime/gdi32_text.cpp` already has full bitmap font rendering for `DrawTextW`/`ExtTextOutW` that can be wired to the ANSI entry points!
     - Check `WM_DRAWITEM` / `WM_MEASUREITEM` / `WM_CTLCOLOR*` for owner-drawn buttons and combo boxes.
2. **Custom Game Cursor (`fn_0040ce20` / `0040cf82`):**
   - `fn_0040ce20` creates a 32×32 cursor bitmap and calls `BitBlt`, which logs `gdi: REFUSED blit dst=00060006(-1x-1)` because `CreateBitmap` / `CreateCompatibleBitmap` on a monochrome/unselected DC isn't producing a valid target DIB. Fixing this will allow custom Worms cursors (and/or forcing software cursor via `[0x0088e3ec] = 0`).
3. **Sub-Menus & Entering a Match (Single Player / Quick Game / Training):**
   - Click through Single Player → Quick Game / Mission / Deathmatch and verify all sub-dialogs, team/map editors, and the actual 2D match engine (`640×480` / higher resolutions, terrain generation, worm physics, weapons, camera scrolling).
4. **Audio (Front-End Music & In-Game SFX):**
   - Verify `DirectSound` (`DSOUND.dll`) + `WINMM` WAV streaming (`DATA/Streams/title.wav`, `FESfx/*.wav`, in-game soundbanks) play cleanly in the browser WebAudio worklet.
5. **Writable Profile / Save Directory Warning:**
   - On startup, `WA.exe` logs `MessageBoxA: Warning: files in the current directory ("C:\WormsArmageddon") are not writable` (auto-dismissed in headless, check behavior in browser OPFS so teams/schemes/replays save properly).
