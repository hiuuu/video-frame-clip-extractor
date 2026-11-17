# Changelog

All notable changes to this project are documented here.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),  
and this project adheres to [Semantic Versioning](https://semver.org/).

## [4.7] — 2026-11-17

### Fixed
- **Right panel scrollbar now visible** — the entire actions column was
  previously placed with `pack(fill="both")` without `expand=True`, giving it
  zero height. The content area now uses `grid` with `rowconfigure(0, weight=1)`
  and `columnconfigure(1, minsize=380)`, so the scrollbar has a real container.
- **Frame slider and step buttons are now smooth and responsive.** Three changes:
  - `-threads 1`, `-an -sn -dn` in the preview FFmpeg command (keeps CPU free for UI)
  - Previous preview FFmpeg process is **killed** before spawning the next one
    (no queue buildup when dragging fast)
  - Preview output is **PPM** instead of PNG — decoding is 4-5× faster, so the
    `PhotoImage` load no longer blocks the UI thread
- **Last/first frame buttons always work.** `_set_slider()` now performs a
  **triple-safe update**: widget-level `frame_slider.set(n)`, variable-level
  `slider_var.set(float(n))`, and explicit `_on_slider_move(n)` callback.
  Whichever path Tk honors, the visual update is guaranteed.

### Added
- **Loading indicator** in the preview area — a small `⏳ Frame N` chip appears
  top-right while a frame is being decoded, so the user knows the app is working.

### Changed
- Preview debounce reduced from 250ms to 150ms — snappier while dragging.

## [4.6.2] — 2026-11-17

### Fixed
- Right-panel scrollbar was rendered on top of the dark background with no
  border or frame, making it nearly invisible. It's now wrapped in a
  `Labelframe` titled **Actions**, matching the left panel's style.
- Explicit `Vertical.TScrollbar` style with `troughcolor=DARKER` and
  `background=SURFACE` — always visible, on any theme.
- Added an 8px bottom spacer inside the scrollable area so the thumb always
  has a bit of travel room.

## [4.6.1] — 2026-11-17

### Fixed
- **Single-step frame buttons (`<` / `>`) didn't move the slider visually.**
  `ttk.Scale.set()` on the widget updates the internal value but, on some Tk
  builds (notably Windows + Python 3.14), doesn't trigger a repaint. The scale
  is now bound to a `tk.DoubleVar`, and updates go through `variable.set()`,
  which Tk guarantees will repaint.

## [4.6] — 2026-11-17

### Added
- **Scrollable right panel** — the action column now scrolls when the window
  is too short. Mouse wheel is bound recursively on every child widget, so
  scrolling works over buttons, entries, sliders, and empty areas alike.
- **Frame navigation bar** — `[<<] [<] ───o─── [>] [>>]`:
  - `<<` jump to first frame
  - `<` step back one frame
  - `>` step forward one frame
  - `>>` jump to last frame
  - Drag the slider in between for coarse selection.

### Changed
- **Compact vertical layout** — paddings reduced throughout, preview shrunk
  from 160px to 130px, drop zone from 44px to 36px, window default height
  from 1000 to 760, minimum from 880 to 550.
- First / Last buttons (v4.5) removed; replaced by the new nav bar.
- `_set_slider(n)` helper added — reliably updates slider, entry, and
  preview even on Tk versions where `ttk.Scale.set()` doesn't fire `command`.

## [4.5] — 2026-11-17

### Added
- **Visual frame preview** in the Frame Extraction section, with a slider to
  scrub through frames. Frames are extracted on-demand via fast `-ss` seek,
  debounced, so dragging remains smooth.
- Slider shows current frame number; typing a number in `Frame #` and pressing
  Enter jumps the slider to that position.

### Changed
- `⏮ First` / `⏭ Last` buttons now **navigate** the slider (helpers), no longer
  extract directly. To extract, click `🖼 Extract This Frame` after navigating.
- `🖼 Extract This Frame` now uses `Accent.TButton` — matches `Extract Clip`
  and `Convert FPS` for a consistent visual hierarchy.
- `hint_label` (estimated total) replaced by `frame_total_label` beside
  the entry: `/ <last>  (<total> frames)`.

## [4.4] — 2026-11-17

### Added
- **Live progress bar** for clip extraction and full-video FPS conversion.
  Uses FFmpeg's `-progress pipe:1 -nostats` protocol and parses `out_time=`
  lines to compute a percentage against the known total duration.
- Status bar and progress bar now share a single bottom frame.

### Changed
- `_run_ffmpeg` signature: `(cmd, msg, total_duration=0.0)`.
- Subprocess I/O is now via `Popen` with `stderr=subprocess.STDOUT` and
  line-buffered iteration, so progress and logs are interleaved correctly.
- `_set_status` / `_set_progress` swallow `TclError`, so closing the window
  mid-operation no longer crashes the background thread.

## [4.3.1] — 2026-11-17

### Fixed
- `NameError: cannot access free variable 'e'` in the Tkinter callback when
  FFmpeg fails or `ffprobe` errors out. The exception variable is now snapshotted
  before being captured by `after(0, ...)` lambdas (Python 3 deletes `e` at the
  end of the `except` block).
- `exit code 4294967295` when probing on Windows — resolved by making the app
  prefer a bundled `ffmpeg.exe` / `ffprobe.exe` next to the script over the
  Chocolatey shim, and by using UTF-8 encoding for subprocess I/O.

## [4.3] — 2026-11-17

### Added
- **Convert Full Video FPS** section — re-encodes an entire video to a target
  frame rate (16 / 24 / 25 / 30 presets + custom value) with optional audio.
  Enforces CFR via `-fps_mode cfr` and outputs H.264 / CRF 18 / yuv420p.
- New output filename pattern: `<name>_converted_<fps>fps_<audio|noaudio>.mp4`

## [4.2] — 2026-11-09

### Added
- Descriptive auto-generated output filenames:
  - `myvideo_clip_from-end_3s_24fps_audio.mp4`
  - `myvideo_frame_first.jpg` / `myvideo_frame_00234.jpg`
- Save dialogs now default to the source video's folder with the filename
  pre-filled.
- `_sanitize` helper strips Windows-invalid characters from filenames.
- Frame numbers in filenames are zero-padded (`zfill(5)`) for correct
  alphabetical sorting.

## [4.1] — 2026-11-09

### Added
- **Paste Path** field as a reliable fallback when drag & drop is blocked.
- DnD registration wrapped in `try/except` — no crashes when Windows blocks drops.

### Fixed
- Regression in v4 where `shlex.split()` destroyed Windows backslashes in
  dropped file paths. Now uses `root.tk.splitlist()`.

## [4.0] — 2026-11-08

### Added
- Version number in window title.
- **Clip start mode** selector: `Beginning` / `End` / `Custom` with custom
  start second.
- Unified **Frame Extraction** panel (first / last / custom in one box).

### Fixed
- Drag & drop now correctly initializes via `TkinterDnD.Tk()` as root; adds
  `_require()` fallback and `TkinterDnD2` import fallback.

## [3.0] — 2026-11-08

### Added
- Custom **clip duration** with quick preset buttons (1 / 3 / 5 / 10).
- Custom **output frame rate** (presets 16 / 24 / 25 / 30 + editable).
- **Include audio** checkbox (default ON).

## [2.0] — 2026-11-08

### Added
- **FPS** in the GENERAL metadata block, using `avg_frame_rate` and
  `r_frame_rate` with CFR/VFR detection.
- Optional **drag & drop** via `tkinterdnd2`.

## [1.0] — 2026-11-08

### Added
- Initial release.
- Full technical metadata via `ffprobe`.
- Clip extraction (last 3 seconds @ 24fps, with/without audio).
- Frame extraction: first / last / custom by number.
