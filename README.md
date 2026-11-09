# 🎬 Video Frame & Clip Extractor

A lightweight, cross-platform desktop app for **extracting clips and frames from videos** — built with Python + Tkinter + FFmpeg. No heavy dependencies, no Electron, no nonsense.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
![License](https://img.shields.io/badge/license-GPL--3.0-blue)
![Version](https://img.shields.io/badge/version-4.2-blueviolet)

---

## ✨ Features

- 🎞 **Clip extraction** from the beginning, the end, or any custom start second
- ⏱ **Custom duration** with quick presets (1s / 3s / 5s / 10s) or any decimal value
- 🎚 **Custom output frame rate** — 16 / 24 / 25 / 30 fps presets or any value you type
- 🔊 **Audio on/off** toggle (AAC 192 kbps when enabled)
- 🖼 **Frame extraction** — first frame, last frame, or any frame by number
- 📊 **Full technical metadata** — codec, resolution, FPS (avg + real + CFR/VFR detection), bitrate, pix_fmt, sample rate, channels, tags, and more
- 📝 **Descriptive auto-generated filenames** (see below)
- 📁 **Optional drag & drop** (requires `tkinterdnd2`; a **Paste Path** field is always available as fallback)
- 🧵 **Non-blocking UI** — all FFmpeg work runs in background threads
- 🎨 **Dark, minimal UI** — Catppuccin-inspired theme, no extra GUI libraries

---

## 📋 Requirements

- **Python 3.10+** (tested up to 3.14.7)
- **FFmpeg** and **FFprobe** available in your system `PATH`
- **tkinterdnd2** _(optional, for drag & drop only)_

---

## 🚀 Installation

### 1. Install Python

Download from [python.org](https://www.python.org/downloads/). On Windows, tick **"Add Python to PATH"** during installation.

### 2. Install FFmpeg

FFmpeg is **required** — the app uses `ffmpeg` and `ffprobe` to process video.

| Platform | Command / Link |
|---|---|
| **Windows** (Chocolatey) | `choco install ffmpeg` |
| **Windows** (winget) | `winget install Gyan.FFmpeg` |
| **Windows** (manual) | [Download from gyan.dev](https://www.gyan.dev/ffmpeg/builds/) → extract → add `bin/` to PATH |
| **macOS** (Homebrew) | `brew install ffmpeg` |
| **Linux** (Debian/Ubuntu) | `sudo apt install ffmpeg` |
| **Linux** (Fedora) | `sudo dnf install ffmpeg` |
| **Linux** (Arch) | `sudo pacman -S ffmpeg` |

**Verify the installation:**

```bash
ffmpeg -version
ffprobe -version
```

Both should print a version banner. If they say "command not found", FFmpeg isn't in your PATH.

### 3. Clone and run

```bash
git clone https://github.com/<your-username>/video-frame-clip-extractor.git
cd video-frame-clip-extractor

# Optional but recommended — use a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
python video_tool.py
```

### 4. (Optional) Enable drag & drop

```bash
pip install tkinterdnd2
```

> ⚠ **Note on Windows:** drag & drop is blocked by Windows' UIPI when the app and Explorer run at different privilege levels (e.g. running the app "as Administrator"). If drag & drop doesn't work, use the **Load Video** button or the **Paste Path** field — both always work. See [Troubleshooting](#-troubleshooting).

---

## 🎯 Usage

### Loading a video

Three ways:

1. Click **📂 Load Video** and pick a file
2. **Paste a path** into the field (or copy it from Explorer with `Shift + Right-click → Copy as path`), then press **Enter** or click **Load Path**
3. **Drag & drop** a video file onto the window _(if `tkinterdnd2` is installed and Windows permits it)_

Once loaded, the left panel shows all technical metadata: codec, resolution, FPS (with **CFR/VFR detection**), bitrate, pixel format, audio sample rate, channels, tags, and an estimated total frame count.

### Extracting a clip

1. Choose **Start from**: `Beginning` / `End` / `Custom`
   - If **Custom**, enter the start second in `Start at (s)`
2. Set **Duration (s)** — use a preset button (`1 / 3 / 5 / 10`) or type any value (`2.5` works)
3. Set **Frame rate** — pick `16 / 24 / 25 / 30` from the dropdown or type any value (`23.976` works)
4. Toggle **Include audio** (on by default)
5. Click **🎬 Extract Clip** and choose where to save

The clip is re-encoded to **H.264 / yuv420p / CFR** at the chosen frame rate, so the output is always playable and VFR-safe.

### Extracting a frame

- **⏮ First Frame** — grabs frame 0
- **⏭ Last Frame** — grabs the final frame (works with `-sseof -1`)
- **🖼 Extract This Frame** — enter any frame number in the `Frame #` field (the estimated total is shown below the field)

Frame images are saved as **JPEG** (quality 2) or **PNG**.

---

## 📝 Output filename convention

All output files are prefixed with the source video's name and suffixed with descriptive English tags, so you can tell exactly what you produced at a glance:

| Action | Example output |
|---|---|
| Clip from end, 3s, 24fps, with audio | `myvideo_clip_from-end_3s_24fps_audio.mp4` |
| Clip from start, 5s, 30fps, no audio | `myvideo_clip_from-start_5s_30fps_noaudio.mp4` |
| Clip from second 15, 2.5s, 24fps, audio | `myvideo_clip_from-15s_2.5s_24fps_audio.mp4` |
| First frame | `myvideo_frame_first.jpg` |
| Last frame | `myvideo_frame_last.jpg` |
| Frame #234 | `myvideo_frame_00234.jpg` |

The save dialog defaults to the **same folder as the source video** and pre-fills the filename. You can always change either before saving.

---

## 🩺 Troubleshooting

### Drag & drop doesn't work

This is usually a **Windows security feature**, not a bug:

- **UIPI (User Interface Privilege Isolation)** blocks drops between apps running at different privilege levels. If you launched the terminal or the app **as Administrator**, drop a video from Explorer into a normal (non-admin) launch of the app instead.
- **Python 3.14.8 on Windows** has a known DnD regression. Downgrade to **3.14.7** if you must use drag & drop.
- **Old `tkinterdnd2`** (0.7.0 from some mirrors) ships Tcl/Tk 8.6 binaries that don't work with Tcl/Tk 9.0 (bundled with Python 3.14). Install from PyPI directly:
  ```bash
  pip install --index-url https://pypi.org/simple/ tkinterdnd2
  ```

**The app always works without drag & drop** — just use **Load Video** or **Paste Path**.

### `ffmpeg not found`

FFmpeg isn't in your `PATH`. Re-install it (see [Install FFmpeg](#2-install-ffmpeg)) and restart your terminal so it picks up the updated `PATH`.

### Output is empty / "frame out of range"

The requested frame number exceeds the video's actual frame count. Check the **Est. total frames** hint below the `Frame #` field.

### Chinese / Persian filenames show as `?`

Make sure you're saving to an NTFS volume and that the terminal encoding is UTF-8. On Windows, `chcp 65001` sets the code page to UTF-8.

---

## 🛠 Tech stack

- **Python 3.10+** — standard library only for the GUI
- **Tkinter** — built-in GUI framework
- **FFmpeg / FFprobe** — all media processing
- **tkinterdnd2** _(optional)_ — drag & drop support

---

## 📄 License

This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)**.

```
Video Frame & Clip Extractor
Copyright (C) 2026 Hamed Zandieh (hamed.zandieh@gmail.com)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
```

### What this means for you

- ✅ **Use freely** — run, study, and modify the source code for any purpose
- ✅ **Redistribute** — share copies with anyone, for free or for a fee
- ⚠️ **Share modifications** — if you distribute a modified version, you **must** release your changes under GPL-3.0 as well
- ⚠️ **Same license downstream** — any derived work distributed to others must also be GPL-3.0
- ❌ **No closed-source forks** — you cannot integrate this code into a proprietary, closed-source product that is distributed to others
- ✅ **Patent grant included** — contributors grant you a license to any patents they hold that are necessary to use the code

The full license text is in the [`LICENSE`](LICENSE) file, or online at
<https://www.gnu.org/licenses/gpl-3.0.html>.

> **Note:** Using the software privately, or as part of an internal (non-distributed) service, does **not** trigger the copyleft obligations. You only need to share source code when you **distribute** the software or a derivative work to others.

---

## 🙏 Acknowledgements

- [FFmpeg](https://ffmpeg.org/) — the engine behind everything (LGPL-2.1+ / GPL-2.0+, depending on build)
- [tkinterdnd2](https://github.com/Eliav2/tkinterdnd2) — optional DnD (MIT)
- [Catppuccin](https://github.com/catppuccin/catppuccin) — color inspiration (MIT)

> FFmpeg is invoked as an external executable and is **not** linked into or bundled with this project's source code, so it does not affect the licensing of this repository. If you distribute a **bundled** copy of FFmpeg with this app, ensure your FFmpeg build's license is compatible with GPL-3.0.

