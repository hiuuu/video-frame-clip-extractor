#!/usr/bin/env python3
# Video Frame & Clip Extractor
# Copyright (C) 2026 Hamed Zandieh (hamed.zandieh@gmail.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
"""
Video Frame & Clip Extractor — v4.7
- Grid layout guarantees visible scrollbar on right panel
- Fast PPM preview (4-5x faster than PNG) with loading indicator
- Previous ffmpeg preview killed on new request (no queue buildup)
- Triple-safe slider update (widget + variable + callback)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess, json, os, threading, shutil, sys, tempfile
from functools import partial

DND_AVAILABLE = False
DND_FILES = None
TkinterDnD = None
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    DND_AVAILABLE = True
except ImportError:
    pass

APP_VERSION = "v4.7"

FFMPEG  = "ffmpeg"
FFPROBE = "ffprobe"


class VideoToolApp:
    BG, FG       = "#1e1e2e", "#cdd6f4"
    ACCENT       = "#89b4fa"
    SURFACE      = "#313244"
    DARKER       = "#181825"
    SUCCESS      = "#a6e3a1"
    ERROR        = "#f38ba8"
    MUTED        = "#9399b2"

    VIDEO_EXTS = {".mp4", ".mkv", ".mov", ".avi", ".webm",
                  ".flv", ".wmv", ".m4v", ".ts", ".mpg", ".mpeg"}
    FPS_PRESETS      = ["16", "24", "25", "30"]
    DURATION_PRESETS = ["1", "3", "5", "10"]
    RIGHT_WIDTH      = 380
    PREVIEW_W        = 320
    PREVIEW_H        = 120

    def __init__(self, root):
        self.root = root
        self.root.title(f"Video Frame & Clip Extractor — {APP_VERSION}")
        self.root.geometry("1120x760")
        self.root.minsize(900, 550)
        self.video_path = None
        self.video_duration = 0.0
        self.total_frames = 0

        self._pending_preview_frame = -1
        self._debounce_job = None
        self._current_preview_path = None
        self._preview_seq = 0
        self._preview_proc = None
        self._right_canvas = None

        self.duration_var     = tk.StringVar(value="3")
        self.fps_var          = tk.StringVar(value="24")
        self.include_audio    = tk.BooleanVar(value=True)
        self.clip_start_mode  = tk.StringVar(value="end")
        self.custom_start_var = tk.StringVar(value="0")
        self.path_input_var   = tk.StringVar()
        self.convert_fps_var  = tk.StringVar(value="24")
        self.convert_audio    = tk.BooleanVar(value=True)
        self.slider_var       = tk.DoubleVar(value=0)

        self._setup_style()
        self._build_ui()
        self._check_dependencies()
        self._setup_dnd()

    # ── Styling ──────────────────────────────────────────────
    def _setup_style(self):
        s = ttk.Style()
        if "clam" in s.theme_names(): s.theme_use("clam")
        self.root.configure(bg=self.BG)
        s.configure(".", background=self.BG, foreground=self.FG)
        s.configure("TFrame", background=self.BG)
        s.configure("TLabel", background=self.BG, foreground=self.FG)
        s.configure("Title.TLabel", background=self.BG, foreground=self.ACCENT,
                    font=("Segoe UI", 15, "bold"))
        s.configure("Mono.TLabel", background=self.BG, foreground=self.FG,
                    font=("Consolas", 9))
        s.configure("Status.TLabel", background=self.DARKER, foreground=self.FG,
                    font=("Consolas", 9), padding=(10, 4))
        s.configure("TButton", background=self.SURFACE, foreground=self.FG,
                    borderwidth=0, padding=(10, 6), font=("Segoe UI", 9))
        s.map("TButton", background=[("active", self.ACCENT)],
              foreground=[("active", self.DARKER)])
        s.configure("Preset.TButton", background=self.DARKER, foreground=self.FG,
                    padding=(4, 3), font=("Consolas", 9))
        s.map("Preset.TButton", background=[("active", self.ACCENT)],
              foreground=[("active", self.DARKER)])
        s.configure("Nav.TButton", background=self.SURFACE, foreground=self.FG,
                    padding=(2, 3), font=("Consolas", 10, "bold"))
        s.map("Nav.TButton", background=[("active", self.ACCENT)],
              foreground=[("active", self.DARKER)])
        s.configure("Accent.TButton", background=self.ACCENT, foreground=self.DARKER,
                    font=("Segoe UI", 10, "bold"), padding=(12, 8))
        s.map("Accent.TButton", background=[("active", "#74c7ec")])
        s.configure("TEntry", fieldbackground=self.SURFACE, foreground=self.FG,
                    insertcolor=self.FG, borderwidth=0, padding=3)
        s.configure("TCombobox", fieldbackground=self.SURFACE, foreground=self.FG,
                    background=self.SURFACE, arrowcolor=self.FG, borderwidth=0,
                    padding=3)
        s.configure("TLabelframe", background=self.BG, foreground=self.ACCENT,
                    borderwidth=1, relief="solid")
        s.configure("TLabelframe.Label", background=self.BG, foreground=self.ACCENT,
                    font=("Segoe UI", 10, "bold"))
        s.configure("TCheckbutton", background=self.BG, foreground=self.FG,
                    font=("Segoe UI", 9))
        s.configure("TRadiobutton", background=self.BG, foreground=self.FG,
                    font=("Segoe UI", 9))
        s.map("TRadiobutton", background=[("active", self.BG)],
              foreground=[("active", self.ACCENT)])
        s.configure("TProgressbar", background=self.ACCENT,
                    troughcolor=self.DARKER, borderwidth=0, thickness=5)
        # Clearly visible scrollbar on dark theme
        s.configure("Vertical.TScrollbar",
                    background=self.SURFACE, troughcolor=self.DARKER,
                    bordercolor=self.BG, arrowcolor=self.FG,
                    darkcolor=self.SURFACE, lightcolor=self.SURFACE,
                    gripcount=0, width=14)
        s.map("Vertical.TScrollbar",
              background=[("active", self.ACCENT), ("pressed", self.ACCENT)])

    # ── UI ────────────────────────────────────────────────────
    def _build_ui(self):
        hdr = ttk.Frame(self.root, padding=(14, 8, 14, 2))
        hdr.pack(fill="x")
        ttk.Label(hdr, text=f"🎬  Video Frame & Clip Extractor  {APP_VERSION}",
                  style="Title.TLabel").pack(side="left")

        self.drop_zone = tk.Frame(self.root, bg=self.SURFACE, height=36,
                                  highlightbackground=self.ACCENT, highlightthickness=1)
        self.drop_zone.pack(fill="x", padx=14, pady=(3, 4))
        self.drop_zone.pack_propagate(False)
        self.drop_label = tk.Label(
            self.drop_zone, text="📁  Drag & drop a video here  (optional)",
            bg=self.SURFACE, fg=self.MUTED, font=("Consolas", 9))
        self.drop_label.pack(expand=True, fill="both")

        load = ttk.Frame(self.root, padding=(14, 0, 14, 6))
        load.pack(fill="x")
        ttk.Button(load, text="📂  Load Video", style="Accent.TButton",
                   command=self.load_video).pack(side="left")
        ttk.Label(load, text="  OR paste path:",
                  style="Mono.TLabel").pack(side="left", padx=(10, 4))
        e = ttk.Entry(load, textvariable=self.path_input_var)
        e.pack(side="left", fill="x", expand=True, padx=(0, 4))
        e.bind("<Return>", lambda _e: self._use_pasted_path())
        ttk.Button(load, text="Load Path",
                   command=self._use_pasted_path).pack(side="left")

        # ── Content area (grid: left grows, right fixed) ─────
        content = ttk.Frame(self.root, padding=(14, 0, 14, 6))
        content.pack(fill="both", expand=True)
        content.columnconfigure(0, weight=1)                    # left grows
        content.columnconfigure(1, weight=0, minsize=self.RIGHT_WIDTH)
        content.rowconfigure(0, weight=1)                       # row grows tall

        # Left: video information
        left = ttk.Labelframe(content, text="  Video Information  ", padding=(8, 5))
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        tc = ttk.Frame(left); tc.pack(fill="both", expand=True)
        self.info_text = tk.Text(tc, bg=self.DARKER, fg=self.FG,
                                 insertbackground=self.FG, font=("Consolas", 9),
                                 relief="flat", wrap="word", state="disabled",
                                 padx=8, pady=6)
        self.info_text.pack(side="left", fill="both", expand=True)
        ys = ttk.Scrollbar(tc, orient="vertical", command=self.info_text.yview)
        ys.pack(side="right", fill="y")
        self.info_text.configure(yscrollcommand=ys.set)

        # Right: scrollable actions panel (gridded, fills row height)
        right_lf = ttk.Labelframe(content, text="  Actions  ", padding=(8, 5))
        right_lf.grid(row=0, column=1, sticky="nsew")

        right_outer = ttk.Frame(right_lf)
        right_outer.pack(fill="both", expand=True)

        self._right_canvas = tk.Canvas(right_outer, bg=self.BG,
                                        highlightthickness=0, borderwidth=0)
        right_scroll = ttk.Scrollbar(right_outer, orient="vertical",
                                     command=self._right_canvas.yview)
        right = ttk.Frame(self._right_canvas)
        right.bind("<Configure>",
                   lambda e: self._right_canvas.configure(
                       scrollregion=self._right_canvas.bbox("all")))
        cwin = self._right_canvas.create_window((0, 0), window=right, anchor="nw")
        self._right_canvas.bind(
            "<Configure>",
            lambda e: self._right_canvas.itemconfig(cwin, width=e.width))
        self._right_canvas.configure(yscrollcommand=right_scroll.set)
        self._right_canvas.pack(side="left", fill="both", expand=True)
        right_scroll.pack(side="right", fill="y")

        # ── Clip Extraction
        clip = ttk.Labelframe(right, text="  Clip Extraction  ", padding=(10, 8))
        clip.pack(fill="x", pady=(0, 6))
        mr = ttk.Frame(clip); mr.pack(fill="x", pady=(0, 3))
        ttk.Label(mr, text="Start from", width=11).pack(side="left")
        for txt, val in (("Beginning", "beginning"), ("End", "end"), ("Custom", "custom")):
            ttk.Radiobutton(mr, text=txt, value=val, variable=self.clip_start_mode,
                            command=self._on_start_mode_change).pack(side="left", padx=(0, 5))
        sr = ttk.Frame(clip); sr.pack(fill="x", pady=(0, 3))
        ttk.Label(sr, text="Start at (s)", width=11).pack(side="left")
        self.custom_start_entry = ttk.Entry(sr, textvariable=self.custom_start_var, width=8)
        self.custom_start_entry.pack(side="left")
        self.custom_start_entry.config(state="disabled")
        dr = ttk.Frame(clip); dr.pack(fill="x", pady=(0, 3))
        ttk.Label(dr, text="Duration (s)", width=11).pack(side="left")
        ttk.Entry(dr, textvariable=self.duration_var, width=6).pack(side="left", padx=(0, 5))
        for v in self.DURATION_PRESETS:
            ttk.Button(dr, text=v, style="Preset.TButton", width=3,
                       command=lambda x=v: self.duration_var.set(x)).pack(side="left", padx=1)
        fr = ttk.Frame(clip); fr.pack(fill="x", pady=(0, 3))
        ttk.Label(fr, text="Frame rate", width=11).pack(side="left")
        ttk.Combobox(fr, textvariable=self.fps_var, values=self.FPS_PRESETS,
                     state="normal", width=8).pack(side="left")
        ttk.Checkbutton(clip, text="Include audio  (AAC 192 kbps)",
                        variable=self.include_audio).pack(anchor="w", pady=(1, 5))
        ttk.Button(clip, text="🎬  Extract Clip", style="Accent.TButton",
                   command=self.extract_clip).pack(fill="x")

        # ── Frame Extraction (preview + slider nav)
        frames = ttk.Labelframe(right, text="  Frame Extraction  ", padding=(10, 8))
        frames.pack(fill="x", pady=(0, 6))

        self.preview_container = tk.Frame(frames, bg=self.DARKER, height=130,
                                          highlightbackground=self.SURFACE,
                                          highlightthickness=1)
        self.preview_container.pack(fill="x", pady=(0, 4))
        self.preview_container.pack_propagate(False)

        self.preview_label = tk.Label(
            self.preview_container, bg=self.DARKER, fg=self.MUTED,
            text="Load a video to preview frames",
            font=("Consolas", 9))
        self.preview_label.place(relx=0.5, rely=0.5, anchor="center")

        # Loading indicator — hidden until needed, placed on top-right corner
        self.loading_label = tk.Label(
            self.preview_container, text="", bg=self.ACCENT, fg=self.DARKER,
            font=("Segoe UI", 8, "bold"), padx=6, pady=1)

        nav_row = ttk.Frame(frames)
        nav_row.pack(fill="x", pady=(0, 3))
        ttk.Button(nav_row, text="<<", style="Nav.TButton", width=3,
                   command=self._goto_first_frame).pack(side="left")
        ttk.Button(nav_row, text="<", style="Nav.TButton", width=2,
                   command=lambda: self._step_frame(-1)).pack(side="left", padx=(2, 4))

        self.frame_slider = ttk.Scale(
            nav_row, from_=0, to=1, orient="horizontal", state="disabled",
            variable=self.slider_var,
            command=self._on_slider_move)
        self.frame_slider.pack(side="left", fill="x", expand=True)

        ttk.Button(nav_row, text=">", style="Nav.TButton", width=2,
                   command=lambda: self._step_frame(1)).pack(side="left", padx=(4, 2))
        ttk.Button(nav_row, text=">>", style="Nav.TButton", width=3,
                   command=self._goto_last_frame).pack(side="left")

        fr_row = ttk.Frame(frames)
        fr_row.pack(fill="x", pady=(0, 5))
        ttk.Label(fr_row, text="Frame").pack(side="left")
        self.frame_entry = ttk.Entry(fr_row, width=8)
        self.frame_entry.pack(side="left", padx=(6, 4))
        self.frame_entry.bind("<Return>", self._on_frame_entry_commit)
        self.frame_total_label = ttk.Label(fr_row, text="/ —", style="Mono.TLabel",
                                            foreground=self.MUTED)
        self.frame_total_label.pack(side="left")

        ttk.Button(frames, text="🖼  Extract This Frame", style="Accent.TButton",
                   command=self.extract_custom_frame).pack(fill="x")

        # ── Full video FPS conversion
        convert = ttk.Labelframe(right, text="  Convert Full Video FPS  ", padding=(10, 8))
        convert.pack(fill="x")
        cfr = ttk.Frame(convert); cfr.pack(fill="x", pady=(0, 3))
        ttk.Label(cfr, text="Target FPS", width=11).pack(side="left")
        ttk.Combobox(cfr, textvariable=self.convert_fps_var, values=self.FPS_PRESETS,
                     state="normal", width=8).pack(side="left")
        cpr = ttk.Frame(convert); cpr.pack(fill="x", pady=(0, 3))
        for v in self.FPS_PRESETS:
            ttk.Button(cpr, text=v, style="Preset.TButton", width=5,
                       command=lambda x=v: self.convert_fps_var.set(x)
                       ).pack(side="left", padx=1, fill="x", expand=True)
        ttk.Checkbutton(convert, text="Include audio  (AAC 192 kbps)",
                        variable=self.convert_audio).pack(anchor="w", pady=(1, 5))
        ttk.Button(convert, text="🎞  Convert FPS", style="Accent.TButton",
                   command=self.convert_fps).pack(fill="x")

        # Bottom spacer — gives the scrollbar travel room
        ttk.Frame(right, height=12).pack(fill="x")

        self._bind_scroll_recursive(right)

        # ── Bottom bar: progress + status
        bottom_bar = ttk.Frame(self.root)
        bottom_bar.pack(fill="x", side="bottom")
        self.progress = ttk.Progressbar(bottom_bar, mode="determinate", maximum=100)
        self.progress.pack(fill="x")
        self.status = ttk.Label(bottom_bar, text="Ready", style="Status.TLabel")
        self.status.pack(fill="x")

    # ── Scroll wheel (recursive) ────────────────────────────
    def _bind_scroll_recursive(self, widget):
        widget.bind("<MouseWheel>", self._on_scroll_wheel)
        widget.bind("<Button-4>", self._on_scroll_wheel)
        widget.bind("<Button-5>", self._on_scroll_wheel)
        for child in widget.winfo_children():
            self._bind_scroll_recursive(child)

    def _on_scroll_wheel(self, event):
        if not self._right_canvas:
            return
        try:
            num = str(getattr(event, "num", ""))
            if num == "4":
                self._right_canvas.yview_scroll(-3, "units")
            elif num == "5":
                self._right_canvas.yview_scroll(3, "units")
            else:
                delta = getattr(event, "delta", 0)
                if delta:
                    steps = int(-delta / 120) * 3
                    if steps == 0:
                        steps = -1 if delta > 0 else 1
                    self._right_canvas.yview_scroll(steps, "units")
        except tk.TclError:
            pass

    def _on_start_mode_change(self):
        self.custom_start_entry.config(
            state="normal" if self.clip_start_mode.get() == "custom" else "disabled")

    # ── DnD ─────────────────────────────────────────────────
    def _setup_dnd(self):
        if not DND_AVAILABLE:
            self.root.after(500, lambda: self._set_status(
                "ℹ  Drag & drop unavailable — use Load Video or Paste Path", self.MUTED))
            return
        self.root.after(250, self._try_register_dnd)

    def _try_register_dnd(self):
        try:
            for w in (self.drop_zone, self.drop_label, self.info_text, self.root):
                w.drop_target_register(DND_FILES)
                w.dnd_bind("<<Drop>>", self._on_drop)
            self._set_status("✅ Drag & drop ready", self.SUCCESS)
            self.root.after(3000, lambda: self._set_status("Ready"))
        except Exception as e:
            print(f"[DND] registration failed: {e}", file=sys.stderr)
            self._set_status("ℹ  DnD blocked by Windows — use Load or Paste Path", self.MUTED)

    def _on_drop(self, event):
        try:
            paths = self.root.tk.splitlist(event.data)
        except Exception:
            paths = [event.data.strip("{}")]
        for p in paths:
            if os.path.isfile(p):
                ext = os.path.splitext(p)[1].lower()
                if ext in self.VIDEO_EXTS:
                    self._load_path(p); return
                messagebox.showwarning("Unsupported",
                                       f"'{os.path.basename(p)}' is not a video.")
                return

    def _use_pasted_path(self):
        raw = self.path_input_var.get().strip().strip('"').strip("'")
        if not raw: return
        if not os.path.isfile(raw):
            messagebox.showerror("File not found", f"Not a valid file:\n{raw}"); return
        ext = os.path.splitext(raw)[1].lower()
        if ext not in self.VIDEO_EXTS:
            messagebox.showwarning("Unsupported",
                                   f"'{os.path.basename(raw)}' is not a video."); return
        self._load_path(raw)

    # ── Binary discovery ─────────────────────────────────────
    @staticmethod
    def _resolve_binary(name):
        ext = ".exe" if sys.platform == "win32" else ""
        exe_name = name + ext
        if getattr(sys, "frozen", False) or "__compiled__" in globals():
            base = os.path.dirname(sys.executable)
        else:
            base = os.path.dirname(os.path.abspath(__file__))
        candidate = os.path.join(base, exe_name)
        if os.path.isfile(candidate):
            return candidate
        if hasattr(sys, "_MEIPASS"):
            candidate = os.path.join(sys._MEIPASS, exe_name)
            if os.path.isfile(candidate):
                return candidate
        return shutil.which(name)

    def _check_dependencies(self):
        global FFMPEG, FFPROBE
        FFMPEG  = self._resolve_binary("ffmpeg")
        FFPROBE = self._resolve_binary("ffprobe")
        for name, path in (("ffmpeg", FFMPEG), ("ffprobe", FFPROBE)):
            if not path or not os.path.isfile(path):
                messagebox.showerror(
                    "Missing dependency",
                    f"'{name}' not found.\n\n"
                    f"Place {name}.exe next to this script,\n"
                    f"or install FFmpeg and add it to PATH.")
                self.root.after(100, self.root.destroy)
                return
        print(f"[FFMPEG ] {FFMPEG}",  file=sys.stderr)
        print(f"[FFPROBE] {FFPROBE}", file=sys.stderr)

    # ── Helpers ──────────────────────────────────────────────
    def _set_info(self, text):
        try:
            self.info_text.config(state="normal")
            self.info_text.delete("1.0", "end")
            self.info_text.insert("end", text)
            self.info_text.config(state="disabled")
        except tk.TclError:
            pass

    def _set_status(self, text, color=None):
        try:
            self.status.config(text=text, foreground=color or self.FG)
        except tk.TclError:
            pass

    def _set_progress(self, pct):
        try:
            self.progress["value"] = max(0.0, min(100.0, float(pct)))
        except (tk.TclError, ValueError):
            pass

    def _reset_progress(self):
        self._set_progress(0.0)

    @staticmethod
    def _parse_hms(time_str):
        try:
            time_str = time_str.strip()
            if not time_str or ":" not in time_str:
                return 0.0
            parts = time_str.split(":")
            if len(parts) == 3:
                h, m, s = parts
                return int(h) * 3600 + int(m) * 60 + float(s)
            if len(parts) == 2:
                m, s = parts
                return int(m) * 60 + float(s)
        except (ValueError, TypeError):
            pass
        return 0.0

    def _require_video(self):
        if not self.video_path:
            messagebox.showwarning("No video", "Please load a video first.")
            return False
        return True

    @staticmethod
    def _sanitize(name, max_len=180):
        bad = '<>:"/\\|?*'
        cleaned = "".join("_" if c in bad else c for c in name).strip()
        return (cleaned or "video")[:max_len]

    def _default_output(self, suffix, ext=".mp4"):
        base_dir = os.path.dirname(self.video_path) or os.getcwd()
        stem = self._sanitize(os.path.splitext(os.path.basename(self.video_path))[0])
        return base_dir, f"{stem}{suffix}{ext}"

    # ── Frame navigation ────────────────────────────────────
    def _set_slider(self, n):
        """Triple-safe slider update — visual update guaranteed."""
        if not self.total_frames:
            return
        n = max(0, min(self.total_frames - 1, int(n)))
        # 1) Widget-level update (guaranteed visual move in all Tk versions)
        try:
            self.frame_slider.set(n)
        except tk.TclError:
            pass
        # 2) Variable-level sync (keeps slider_var consistent)
        try:
            self.slider_var.set(float(n))
        except tk.TclError:
            pass
        # 3) Explicit callback (updates entry + schedules preview)
        self._on_slider_move(n)

    def _goto_first_frame(self):
        self._set_slider(0)

    def _goto_last_frame(self):
        if self.total_frames:
            self._set_slider(self.total_frames - 1)

    def _step_frame(self, delta):
        if not self.total_frames:
            return
        try:
            cur = int(float(self.slider_var.get()))
        except (ValueError, tk.TclError):
            cur = 0
        self._set_slider(cur + delta)

    def _on_slider_move(self, value):
        if not self.total_frames:
            return
        try:
            n = int(float(value))
        except (ValueError, TypeError):
            return
        if n < 0: n = 0
        if n >= self.total_frames: n = self.total_frames - 1
        if self.frame_entry.get() != str(n):
            self.frame_entry.delete(0, "end")
            self.frame_entry.insert(0, str(n))
        self._schedule_preview(n)

    def _on_frame_entry_commit(self, event=None):
        raw = self.frame_entry.get().strip()
        if not raw.isdigit() or not self.total_frames:
            return
        n = int(raw)
        if 0 <= n < self.total_frames:
            self._set_slider(n)

    # ── Preview pipeline ────────────────────────────────────
    def _schedule_preview(self, frame_n):
        if self._debounce_job:
            try:
                self.root.after_cancel(self._debounce_job)
            except Exception:
                pass
        self._debounce_job = self.root.after(
            150, lambda: self._update_preview(frame_n))

    def _show_loading(self, frame_n):
        if self._pending_preview_frame != frame_n:
            return
        try:
            self.loading_label.config(text=f"⏳ Frame {frame_n}")
            self.loading_label.lift()
            self.loading_label.place(relx=1.0, rely=0.0, anchor="ne", x=-4, y=4)
        except tk.TclError:
            pass

    def _hide_loading(self):
        try:
            self.loading_label.place_forget()
        except tk.TclError:
            pass

    def _update_preview(self, frame_n):
        if not self.video_path or self.total_frames <= 0:
            return
        self._pending_preview_frame = frame_n

        # Kill previous ffmpeg if still running — prevents queue buildup
        old = self._preview_proc
        if old is not None and old.poll() is None:
            try: old.kill()
            except Exception: pass

        # Show loading indicator immediately
        self.root.after(0, partial(self._show_loading, frame_n))

        self._preview_seq += 1
        tmp = os.path.join(
            tempfile.gettempdir(), f"vfe_preview_{self._preview_seq}.ppm")

        denom = max(1, self.total_frames - 1)
        ts = (frame_n / denom) * max(0.0, self.video_duration)
        if self.video_duration > 0:
            ts = min(ts, max(0.0, self.video_duration - 0.05))

        cmd = [FFMPEG, "-y",
               "-ss", f"{ts:.3f}",
               "-i", self.video_path,
               "-frames:v", "1",
               "-an", "-sn", "-dn",           # skip non-video streams
               "-threads", "1",               # keep CPU for UI
               "-vf", f"scale={self.PREVIEW_W}:{self.PREVIEW_H}"
                      ":force_original_aspect_ratio=decrease",
               "-c:v", "ppm",                 # PPM decode is 4-5x faster than PNG
               tmp]

        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"[preview] Popen failed: {e}", file=sys.stderr)
            self.root.after(0, self._hide_loading)
            return
        self._preview_proc = proc

        def work():
            try:
                proc.wait(timeout=10)
                if proc.returncode == 0 and os.path.exists(tmp):
                    if self._pending_preview_frame == frame_n:
                        self.root.after(0, partial(self._display_preview, tmp, frame_n))
                    else:
                        try: os.remove(tmp)
                        except Exception: pass
                else:
                    try: os.remove(tmp)
                    except Exception: pass
            except subprocess.TimeoutExpired:
                try: proc.kill()
                except Exception: pass
                self.root.after(0, self._hide_loading)
            except Exception as e:
                print(f"[preview] {e}", file=sys.stderr)
                try: os.remove(tmp)
                except Exception: pass
                self.root.after(0, self._hide_loading)

        threading.Thread(target=work, daemon=True).start()

    def _display_preview(self, path, frame_n):
        self._hide_loading()
        if self._pending_preview_frame != frame_n:
            try: os.remove(path)
            except Exception: pass
            return
        try:
            img = tk.PhotoImage(file=path)
            self.preview_label.config(image=img, text="", fg=self.FG)
            self.preview_label.image = img
            if self._current_preview_path and self._current_preview_path != path:
                try: os.remove(self._current_preview_path)
                except Exception: pass
            self._current_preview_path = path
        except tk.TclError as e:
            print(f"[preview] PhotoImage failed: {e}", file=sys.stderr)
            self.preview_label.config(
                image="", text=f"⚠ Preview unavailable\n({type(e).__name__})",
                fg=self.ERROR)
            self.preview_label.image = None
            try: os.remove(path)
            except Exception: pass

    # ── Load & probe ─────────────────────────────────────────
    def load_video(self):
        p = filedialog.askopenfilename(
            title="Select video",
            filetypes=[("Video", "*.mp4 *.mkv *.mov *.avi *.webm *.flv *.wmv *.m4v *.ts"),
                       ("All", "*.*")])
        if p: self._load_path(p)

    def _load_path(self, path):
        self.video_path = path
        self.video_duration = 0.0
        self.total_frames = 0
        self._pending_preview_frame = -1
        if self._debounce_job:
            try: self.root.after_cancel(self._debounce_job)
            except Exception: pass
            self._debounce_job = None
        if self._preview_proc and self._preview_proc.poll() is None:
            try: self._preview_proc.kill()
            except Exception: pass
        self._preview_proc = None
        if self._current_preview_path:
            try: os.remove(self._current_preview_path)
            except Exception: pass
            self._current_preview_path = None
        self.frame_slider.config(state="disabled")
        try: self.slider_var.set(0)
        except tk.TclError: pass
        self.frame_entry.delete(0, "end")
        self.frame_total_label.config(text="/ —", foreground=self.MUTED)
        self.preview_label.config(image="", text="Loading preview…", fg=self.MUTED)
        self.preview_label.image = None
        self._hide_loading()

        self.path_input_var.set(path)
        self.drop_label.config(text=f"📁  {path}", fg=self.FG)
        self._set_info("Loading…\n")
        self._set_status("Probing video…")
        threading.Thread(target=self._probe_video, daemon=True).start()

    def _probe_video(self):
        try:
            proc = subprocess.run(
                [FFPROBE, "-v", "error", "-print_format", "json",
                 "-show_format", "-show_streams", self.video_path],
                capture_output=True, text=True, timeout=60,
                encoding="utf-8", errors="replace")
            if proc.returncode != 0:
                err = (proc.stderr or "").strip() or f"exit code {proc.returncode}"
                raise RuntimeError(
                    f"ffprobe failed (exit {proc.returncode})\n"
                    f"Binary : {FFPROBE}\n"
                    f"File   : {self.video_path}\n"
                    f"Stderr : {err[:2000]}")
            try:
                data = json.loads(proc.stdout)
            except json.JSONDecodeError as je:
                raise RuntimeError(
                    f"ffprobe returned non-JSON output:\n{je}\n"
                    f"Raw (first 500): {proc.stdout[:500]}")
            self.root.after(0, self._render_info, data)
        except subprocess.TimeoutExpired:
            self.root.after(0, partial(self._set_info,
                f"ffprobe timed out\nBinary: {FFPROBE}\nFile: {self.video_path}"))
        except Exception as e:
            self.root.after(0, partial(self._set_info, f"Error probing video:\n{e}\n"))

    # ── FPS / format helpers ─────────────────────────────────
    @staticmethod
    def _get_video_stream(data):
        for s in data.get("streams", []):
            if s.get("codec_type") == "video": return s
        return None

    @staticmethod
    def _parse_rate(rs):
        if not rs or rs in ("0/0", "N/A"): return None
        try:
            n, d = rs.split("/"); d = float(d)
            return None if d == 0 else float(n) / d
        except Exception:
            try: return float(rs)
            except Exception: return None

    @classmethod
    def _fmt_fps(cls, vs):
        if not vs: return "N/A"
        a = cls._parse_rate(vs.get("avg_frame_rate"))
        r = cls._parse_rate(vs.get("r_frame_rate"))
        if a is None and r is None: return "N/A"
        p = []
        if a is not None: p.append(f"{a:.3f} fps (avg={vs.get('avg_frame_rate')})")
        if r is not None and r != a: p.append(f"{r:.3f} fps (real={vs.get('r_frame_rate')})")
        note = ""
        if a is not None and r is not None:
            if r > a * 1.05: note = "  ⚠ VFR suspected"
            elif abs(r - a) < 0.01: note = "  ✓ CFR"
        return " | ".join(p) + note

    def _render_info(self, data):
        fmt = data.get("format", {}); ss = data.get("streams", [])
        vs = self._get_video_stream(data)
        total = self._estimate_frames(data)
        try:
            self.video_duration = float(fmt.get("duration") or 0.0)
        except (TypeError, ValueError):
            self.video_duration = 0.0
        self.total_frames = total

        out, sep = [], "─" * 66
        out.append(sep); out.append("  ▶  GENERAL"); out.append(sep)
        out.append(f"  File         : {os.path.basename(self.video_path)}")
        out.append(f"  Path         : {self.video_path}")
        out.append(f"  Size         : {self._fmt_size(fmt.get('size'))}")
        out.append(f"  Duration     : {self._fmt_duration(fmt.get('duration'))}")
        out.append(f"  Overall BR   : {self._fmt_bitrate(fmt.get('bit_rate'))}")
        out.append(f"  Format       : {fmt.get('format_long_name', 'N/A')}")
        out.append(f"  Streams      : {len(ss)}")
        if vs:
            out.append(f"  FPS          : {self._fmt_fps(vs)}")
            if vs.get("width") and vs.get("height"):
                out.append(f"  Resolution   : {vs['width']}×{vs['height']}")
            out.append(f"  Video codec  : {vs.get('codec_name','N/A')} "
                       f"({vs.get('profile','N/A')})")
            if vs.get("bit_rate"):
                out.append(f"  Video BR     : {self._fmt_bitrate(vs['bit_rate'])}")
        if total: out.append(f"  Est. frames  : {total:,}")
        out.append("")

        for i, s in enumerate(ss):
            out.append(sep)
            out.append(f"  ▶  STREAM #{i} — {s.get('codec_type','?').upper()}")
            out.append(sep)
            for k, v in s.items():
                if k in ("disposition", "tags"): continue
                out.append(f"  {k:<22}: {json.dumps(v) if isinstance(v, dict) else v}")
            for tk_, tv in (s.get("tags") or {}).items():
                out.append(f"  tag:{tk_:<18}: {tv}")
            out.append("")
        self._set_info("\n".join(out))
        self._set_status(f"Loaded: {os.path.basename(self.video_path)}")

        if total > 0:
            self.frame_slider.config(from_=0, to=total - 1, state="normal")
            self.frame_entry.delete(0, "end")
            self.frame_entry.insert(0, "0")
            self.frame_total_label.config(
                text=f"/ {total - 1}  ({total:,} frames)", foreground=self.FG)
            self._set_slider(0)
        else:
            self.frame_slider.config(state="disabled")
            self.frame_total_label.config(text="/ —", foreground=self.MUTED)
            self.preview_label.config(image="", text="No frames", fg=self.MUTED)
            self.preview_label.image = None

    @staticmethod
    def _fmt_size(b):
        try: b = float(b)
        except Exception: return "N/A"
        for u in ("B","KB","MB","GB","TB"):
            if b < 1024: return f"{b:.2f} {u}"
            b /= 1024
        return f"{b:.2f} PB"

    @staticmethod
    def _fmt_duration(s):
        try: s = float(s)
        except Exception: return "N/A"
        return f"{int(s//3600):02d}:{int((s%3600)//60):02d}:{s%60:06.3f}  ({s:.3f}s)"

    @staticmethod
    def _fmt_bitrate(b):
        try: return f"{float(b)/1000:.0f} kbps"
        except Exception: return "N/A"

    @classmethod
    def _estimate_frames(cls, data):
        try:
            dur = float(data["format"]["duration"])
            vs = cls._get_video_stream(data)
            fps = cls._parse_rate(vs.get("avg_frame_rate")) if vs else None
            return int(dur * fps) if fps else 0
        except Exception:
            return 0

    @staticmethod
    def _num(x):
        return str(int(x)) if x == int(x) else f"{x:g}"

    # ── Clip extraction ──────────────────────────────────────
    def extract_clip(self):
        if not self._require_video(): return
        try:
            dur = float(self.duration_var.get().strip())
            if dur <= 0: raise ValueError
        except Exception:
            messagebox.showerror("Invalid", "Duration must be > 0."); return
        try:
            fps = float(self.fps_var.get().strip())
            if fps <= 0: raise ValueError
        except Exception:
            messagebox.showerror("Invalid", "Frame rate must be > 0."); return

        mode = self.clip_start_mode.get()
        start = 0.0
        if mode == "custom":
            try:
                start = float(self.custom_start_var.get().strip())
                if start < 0: raise ValueError
            except Exception:
                messagebox.showerror("Invalid", "Start time must be >= 0."); return

        with_audio = self.include_audio.get()
        ds, fs = self._num(dur), self._num(fps)
        mode_part = {"beginning": "from-start", "end": "from-end",
                     "custom": f"from-{self._num(start)}s"}[mode]
        audio_part = "audio" if with_audio else "noaudio"
        suffix = f"_clip_{mode_part}_{ds}s_{fs}fps_{audio_part}"
        initdir, initfile = self._default_output(suffix, ".mp4")

        out = filedialog.asksaveasfilename(
            title=f"Save {ds}s @ {fs}fps clip as…",
            initialdir=initdir, initialfile=initfile,
            defaultextension=".mp4", filetypes=[("MP4 video", "*.mp4")])
        if not out: return

        seek = (["-sseof", f"-{ds}"] if mode == "end"
                else ["-ss", self._num(start)])
        audio = ["-c:a", "aac", "-b:a", "192k"] if with_audio else ["-an"]
        cmd = ["ffmpeg", "-y"] + seek + [
            "-i", self.video_path, "-t", ds,
            "-vf", f"fps={fs}", "-fps_mode", "cfr",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-pix_fmt", "yuv420p"] + audio + [out]

        lbl = {"beginning": "from beginning", "end": "from end",
               "custom": f"from {self._num(start)}s"}[mode]
        self._run_ffmpeg(cmd, f"Extracting {ds}s @ {fs}fps {lbl} "
                              f"({'with' if with_audio else 'without'} audio)…",
                         total_duration=dur)

    # ── Frame extraction ─────────────────────────────────────
    def extract_custom_frame(self):
        if not self._require_video(): return
        raw = self.frame_entry.get().strip()
        if not raw.isdigit():
            messagebox.showerror("Invalid", "Frame must be a non-negative integer.")
            return
        n = int(raw)
        initdir, initfile = self._default_output(f"_frame_{n:05d}", ".jpg")
        out = filedialog.asksaveasfilename(
            title=f"Save frame #{n} as…",
            initialdir=initdir, initialfile=initfile,
            defaultextension=".jpg",
            filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png")])
        if not out: return
        self._run_ffmpeg(
            ["ffmpeg", "-y", "-i", self.video_path,
             "-vf", f"select=eq(n\\,{n})", "-frames:v", "1", "-q:v", "2", out],
            f"Extracting frame #{n}…")

    # ── Full video FPS conversion ───────────────────────────
    def convert_fps(self):
        if not self._require_video(): return
        try:
            fps = float(self.convert_fps_var.get().strip())
            if fps <= 0: raise ValueError
        except Exception:
            messagebox.showerror("Invalid", "Frame rate must be > 0."); return

        with_audio = self.convert_audio.get()
        fs = self._num(fps)
        audio_part = "audio" if with_audio else "noaudio"
        suffix = f"_converted_{fs}fps_{audio_part}"
        initdir, initfile = self._default_output(suffix, ".mp4")

        out = filedialog.asksaveasfilename(
            title=f"Convert full video to {fs}fps as…",
            initialdir=initdir, initialfile=initfile,
            defaultextension=".mp4", filetypes=[("MP4 video", "*.mp4")])
        if not out: return

        audio = ["-c:a", "aac", "-b:a", "192k"] if with_audio else ["-an"]
        cmd = ["ffmpeg", "-y",
               "-i", self.video_path,
               "-vf", f"fps={fs}", "-fps_mode", "cfr",
               "-c:v", "libx264", "-preset", "medium", "-crf", "18",
               "-pix_fmt", "yuv420p"] + audio + [out]

        self._run_ffmpeg(
            cmd,
            f"Converting full video to {fs}fps "
            f"({'with' if with_audio else 'without'} audio)…",
            total_duration=self.video_duration)

    # ── FFmpeg runner ────────────────────────────────────────
    def _run_ffmpeg(self, cmd, msg, total_duration=0.0):
        self._set_status(msg)
        self._reset_progress()
        if cmd and cmd[0] == "ffmpeg":
            cmd = [FFMPEG] + cmd[1:]
        out = cmd[-1]
        if total_duration > 0:
            cmd = cmd[:-1] + ["-progress", "pipe:1", "-nostats", out]

        progress_keys = {"frame", "fps", "bitrate", "total_size",
                         "out_time_us", "out_time_ms",
                         "dup_frames", "drop_frames", "speed"}

        def work():
            try:
                proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, encoding="utf-8", errors="replace", bufsize=1)
                log_lines = []
                for raw in proc.stdout:
                    line = raw.rstrip("\r\n")
                    if not line:
                        continue
                    if total_duration > 0:
                        if line.startswith("out_time="):
                            t = self._parse_hms(line.split("=", 1)[1])
                            pct = min(100.0, (t / total_duration) * 100.0)
                            self.root.after(0, partial(self._set_progress, pct))
                            continue
                        if line.startswith("progress="):
                            if line.strip() == "progress=end":
                                self.root.after(0, partial(self._set_progress, 100.0))
                            continue
                        if "=" in line:
                            key = line.split("=", 1)[0]
                            if key in progress_keys or key.startswith("stream_"):
                                continue
                    log_lines.append(line)
                proc.wait()
                if proc.returncode != 0:
                    tail = "\n".join(log_lines[-20:])
                    raise RuntimeError(
                        f"FFmpeg failed (exit {proc.returncode})\n"
                        f"Binary : {FFMPEG}\n"
                        f"Stderr :\n{tail or '(empty)'}")
                if not os.path.exists(out) or os.path.getsize(out) == 0:
                    raise RuntimeError(
                        "FFmpeg returned success but output is missing/empty.\n"
                        "The requested frame may be out of range.")
                self.root.after(0, partial(self._set_progress, 100.0))
                self.root.after(0, partial(self._set_status,
                                           f"✅ Done → {out}", self.SUCCESS))
                self.root.after(0, partial(messagebox.showinfo,
                                           "Success", f"Saved:\n{out}"))
            except Exception as e:
                err_msg = str(e)
                self.root.after(0, partial(self._set_progress, 0.0))
                self.root.after(0, partial(self._set_status, "❌ Failed", self.ERROR))
                self.root.after(0, partial(messagebox.showerror,
                                           "FFmpeg error", err_msg))
        threading.Thread(target=work, daemon=True).start()


if __name__ == "__main__":
    root = TkinterDnD.Tk() if DND_AVAILABLE else tk.Tk()
    VideoToolApp(root)
    root.mainloop()
