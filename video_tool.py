#!/usr/bin/env python3
"""
Video Frame & Clip Extractor — v4.2
Final version with descriptive output filenames.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess, json, os, threading, shutil, sys

DND_AVAILABLE = False
DND_FILES = None
TkinterDnD = None
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    DND_AVAILABLE = True
except ImportError:
    pass

APP_VERSION = "v4.2"


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

    def __init__(self, root):
        self.root = root
        self.root.title(f"Video Frame & Clip Extractor — {APP_VERSION}")
        self.root.geometry("1140x840")
        self.root.minsize(1000, 740)
        self.video_path = None

        self.duration_var     = tk.StringVar(value="3")
        self.fps_var          = tk.StringVar(value="24")
        self.include_audio    = tk.BooleanVar(value=True)
        self.clip_start_mode  = tk.StringVar(value="end")
        self.custom_start_var = tk.StringVar(value="0")
        self.path_input_var   = tk.StringVar()

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
                    font=("Segoe UI", 16, "bold"))
        s.configure("Mono.TLabel", background=self.BG, foreground=self.FG,
                    font=("Consolas", 9))
        s.configure("Status.TLabel", background=self.DARKER, foreground=self.FG,
                    font=("Consolas", 9), padding=(10, 5))
        s.configure("TButton", background=self.SURFACE, foreground=self.FG,
                    borderwidth=0, padding=(10, 7), font=("Segoe UI", 9))
        s.map("TButton", background=[("active", self.ACCENT)],
              foreground=[("active", self.DARKER)])
        s.configure("Preset.TButton", background=self.DARKER, foreground=self.FG,
                    padding=(4, 4), font=("Consolas", 9))
        s.map("Preset.TButton", background=[("active", self.ACCENT)],
              foreground=[("active", self.DARKER)])
        s.configure("Accent.TButton", background=self.ACCENT, foreground=self.DARKER,
                    font=("Segoe UI", 10, "bold"), padding=(12, 9))
        s.map("Accent.TButton", background=[("active", "#74c7ec")])
        s.configure("TEntry", fieldbackground=self.SURFACE, foreground=self.FG,
                    insertcolor=self.FG, borderwidth=0, padding=4)
        s.configure("TCombobox", fieldbackground=self.SURFACE, foreground=self.FG,
                    background=self.SURFACE, arrowcolor=self.FG, borderwidth=0,
                    padding=4)
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

    # ── UI ────────────────────────────────────────────────────
    def _build_ui(self):
        hdr = ttk.Frame(self.root, padding=(16, 12, 16, 4))
        hdr.pack(fill="x")
        ttk.Label(hdr, text=f"🎬  Video Frame & Clip Extractor  {APP_VERSION}",
                  style="Title.TLabel").pack(side="left")

        self.drop_zone = tk.Frame(self.root, bg=self.SURFACE, height=44,
                                  highlightbackground=self.ACCENT, highlightthickness=1)
        self.drop_zone.pack(fill="x", padx=16, pady=(4, 6))
        self.drop_zone.pack_propagate(False)
        self.drop_label = tk.Label(
            self.drop_zone, text="📁  Drag & drop a video here  (optional — see fallback below)",
            bg=self.SURFACE, fg=self.MUTED, font=("Consolas", 10))
        self.drop_label.pack(expand=True, fill="both")

        load = ttk.Frame(self.root, padding=(16, 0, 16, 8))
        load.pack(fill="x")
        ttk.Button(load, text="📂  Load Video", style="Accent.TButton",
                   command=self.load_video).pack(side="left")
        ttk.Label(load, text="  OR paste path:",
                  style="Mono.TLabel").pack(side="left", padx=(12, 4))
        e = ttk.Entry(load, textvariable=self.path_input_var)
        e.pack(side="left", fill="x", expand=True, padx=(0, 4))
        e.bind("<Return>", lambda _e: self._use_pasted_path())
        ttk.Button(load, text="Load Path",
                   command=self._use_pasted_path).pack(side="left")

        content = ttk.Frame(self.root, padding=(16, 0, 16, 8))
        content.pack(fill="both", expand=True)

        left = ttk.Labelframe(content, text="  Video Information  ", padding=10)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        tc = ttk.Frame(left); tc.pack(fill="both", expand=True)
        self.info_text = tk.Text(tc, bg=self.DARKER, fg=self.FG,
                                 insertbackground=self.FG, font=("Consolas", 9),
                                 relief="flat", wrap="word", state="disabled",
                                 padx=8, pady=6)
        self.info_text.pack(side="left", fill="both", expand=True)
        ys = ttk.Scrollbar(tc, orient="vertical", command=self.info_text.yview)
        ys.pack(side="right", fill="y")
        self.info_text.configure(yscrollcommand=ys.set)

        right = ttk.Frame(content, width=380)
        right.pack(side="right", fill="y"); right.pack_propagate(False)

        clip = ttk.Labelframe(right, text="  Clip Extraction  ", padding=12)
        clip.pack(fill="x", pady=(0, 10))
        mr = ttk.Frame(clip); mr.pack(fill="x", pady=(0, 4))
        ttk.Label(mr, text="Start from", width=12).pack(side="left")
        for txt, val in (("Beginning", "beginning"), ("End", "end"), ("Custom", "custom")):
            ttk.Radiobutton(mr, text=txt, value=val, variable=self.clip_start_mode,
                            command=self._on_start_mode_change).pack(side="left", padx=(0, 6))
        sr = ttk.Frame(clip); sr.pack(fill="x", pady=(0, 6))
        ttk.Label(sr, text="Start at (s)", width=12).pack(side="left")
        self.custom_start_entry = ttk.Entry(sr, textvariable=self.custom_start_var, width=8)
        self.custom_start_entry.pack(side="left")
        self.custom_start_entry.config(state="disabled")
        dr = ttk.Frame(clip); dr.pack(fill="x", pady=(0, 6))
        ttk.Label(dr, text="Duration (s)", width=12).pack(side="left")
        ttk.Entry(dr, textvariable=self.duration_var, width=6).pack(side="left", padx=(0, 6))
        for v in self.DURATION_PRESETS:
            ttk.Button(dr, text=v, style="Preset.TButton", width=3,
                       command=lambda x=v: self.duration_var.set(x)).pack(side="left", padx=1)
        fr = ttk.Frame(clip); fr.pack(fill="x", pady=(0, 6))
        ttk.Label(fr, text="Frame rate", width=12).pack(side="left")
        ttk.Combobox(fr, textvariable=self.fps_var, values=self.FPS_PRESETS,
                     state="normal", width=8).pack(side="left")
        ttk.Checkbutton(clip, text="Include audio  (AAC 192 kbps)",
                        variable=self.include_audio).pack(anchor="w", pady=(2, 8))
        ttk.Button(clip, text="🎬  Extract Clip", style="Accent.TButton",
                   command=self.extract_clip).pack(fill="x")

        frames = ttk.Labelframe(right, text="  Frame Extraction  ", padding=12)
        frames.pack(fill="x")
        fl = ttk.Frame(frames); fl.pack(fill="x", pady=(0, 8))
        ttk.Button(fl, text="⏮  First Frame",
                   command=self.extract_first_frame).pack(side="left", expand=True, fill="x")
        ttk.Button(fl, text="⏭  Last Frame",
                   command=self.extract_last_frame).pack(side="left", expand=True,
                                                        fill="x", padx=(8, 0))
        ttk.Separator(frames, orient="horizontal").pack(fill="x", pady=(0, 8))
        cr = ttk.Frame(frames); cr.pack(fill="x", pady=(0, 4))
        ttk.Label(cr, text="Frame #").pack(side="left")
        self.frame_entry = ttk.Entry(cr)
        self.frame_entry.pack(side="left", padx=(8, 0), fill="x", expand=True)
        self.hint_label = ttk.Label(frames, text="", style="Mono.TLabel",
                                    foreground=self.MUTED)
        self.hint_label.pack(fill="x", pady=(0, 6))
        ttk.Button(frames, text="🖼  Extract This Frame",
                   command=self.extract_custom_frame).pack(fill="x")

        self.status = ttk.Label(self.root, text="Ready", style="Status.TLabel")
        self.status.pack(fill="x", side="bottom")

    def _on_start_mode_change(self):
        self.custom_start_entry.config(
            state="normal" if self.clip_start_mode.get() == "custom" else "disabled")

    # ── DnD — safe wrapper ───────────────────────────────────
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

    # ── Dependency check ─────────────────────────────────────
    def _check_dependencies(self):
        for tool in ("ffmpeg", "ffprobe"):
            if not shutil.which(tool):
                messagebox.showerror("Missing dependency",
                    f"'{tool}' not found in PATH.\nInstall FFmpeg.")
                self.root.after(100, self.root.destroy); return

    # ── Helpers ──────────────────────────────────────────────
    def _set_info(self, text):
        self.info_text.config(state="normal")
        self.info_text.delete("1.0", "end")
        self.info_text.insert("end", text)
        self.info_text.config(state="disabled")

    def _set_status(self, text, color=None):
        self.status.config(text=text, foreground=color or self.FG)

    def _require_video(self):
        if not self.video_path:
            messagebox.showwarning("No video", "Please load a video first.")
            return False
        return True

    @staticmethod
    def _sanitize(name, max_len=180):
        """Remove chars invalid on Windows; keep Persian/Unicode intact."""
        bad = '<>:"/\\|?*'
        cleaned = "".join("_" if c in bad else c for c in name).strip()
        return (cleaned or "video")[:max_len]

    def _default_output(self, suffix, ext=".mp4"):
        """Return (initialdir, initialfile) for save dialogs."""
        base_dir = os.path.dirname(self.video_path) or os.getcwd()
        stem = self._sanitize(os.path.splitext(os.path.basename(self.video_path))[0])
        return base_dir, f"{stem}{suffix}{ext}"

    # ── Load & probe ─────────────────────────────────────────
    def load_video(self):
        p = filedialog.askopenfilename(
            title="Select video",
            filetypes=[("Video", "*.mp4 *.mkv *.mov *.avi *.webm *.flv *.wmv *.m4v *.ts"),
                       ("All", "*.*")])
        if p: self._load_path(p)

    def _load_path(self, path):
        self.video_path = path
        self.path_input_var.set(path)
        self.drop_label.config(text=f"📁  {path}", fg=self.FG)
        self._set_info("Loading…\n")
        self._set_status("Probing video…")
        threading.Thread(target=self._probe_video, daemon=True).start()

    def _probe_video(self):
        try:
            proc = subprocess.run(
                ["ffprobe", "-v", "error", "-print_format", "json",
                 "-show_format", "-show_streams", self.video_path],
                capture_output=True, text=True, check=True)
            data = json.loads(proc.stdout)
            self.root.after(0, self._render_info, data)
        except Exception as e:
            self.root.after(0, lambda: self._set_info(f"Error:\n{e}\n"))

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
        self.hint_label.config(text=f"Est. total frames: {total:,}" if total else "")

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

        # ── Build descriptive filename ─────────────────────
        mode_part = {
            "beginning": "from-start",
            "end":       "from-end",
            "custom":    f"from-{self._num(start)}s",
        }[mode]
        audio_part = "audio" if with_audio else "noaudio"
        suffix = f"_clip_{mode_part}_{ds}s_{fs}fps_{audio_part}"
        initdir, initfile = self._default_output(suffix, ".mp4")

        out = filedialog.asksaveasfilename(
            title=f"Save {ds}s @ {fs}fps clip as…",
            initialdir=initdir, initialfile=initfile,
            defaultextension=".mp4",
            filetypes=[("MP4 video", "*.mp4")])
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
                              f"({'with' if with_audio else 'without'} audio)…")

    # ── Frame extraction ─────────────────────────────────────
    def extract_first_frame(self):
        if not self._require_video(): return
        initdir, initfile = self._default_output("_frame_first", ".jpg")
        out = filedialog.asksaveasfilename(
            title="Save first frame as…",
            initialdir=initdir, initialfile=initfile,
            defaultextension=".jpg",
            filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png")])
        if not out: return
        self._run_ffmpeg(
            ["ffmpeg", "-y", "-i", self.video_path,
             "-vf", "select=eq(n\\,0)", "-frames:v", "1", "-q:v", "2", out],
            "Extracting first frame…")

    def extract_last_frame(self):
        if not self._require_video(): return
        initdir, initfile = self._default_output("_frame_last", ".jpg")
        out = filedialog.asksaveasfilename(
            title="Save last frame as…",
            initialdir=initdir, initialfile=initfile,
            defaultextension=".jpg",
            filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png")])
        if not out: return
        self._run_ffmpeg(
            ["ffmpeg", "-y", "-sseof", "-1", "-i", self.video_path,
             "-update", "1", "-q:v", "2", out],
            "Extracting last frame…")

    def extract_custom_frame(self):
        if not self._require_video(): return
        raw = self.frame_entry.get().strip()
        if not raw.isdigit():
            messagebox.showerror("Invalid", "Frame must be a non-negative integer."); return
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

    # ── FFmpeg runner ────────────────────────────────────────
    def _run_ffmpeg(self, cmd, msg):
        self._set_status(msg)
        out = cmd[-1]
        def work():
            try:
                p = subprocess.run(cmd, capture_output=True, text=True)
                if p.returncode != 0:
                    tail = "\n".join(p.stderr.strip().splitlines()[-15:])
                    raise RuntimeError(tail or "FFmpeg error")
                if not os.path.exists(out) or os.path.getsize(out) == 0:
                    raise RuntimeError("Output missing/empty (frame out of range?)")
                self.root.after(0, lambda: self._set_status(f"✅ Done → {out}", self.SUCCESS))
                self.root.after(0, lambda: messagebox.showinfo("Success", f"Saved:\n{out}"))
            except Exception as e:
                self.root.after(0, lambda: self._set_status("❌ Failed", self.ERROR))
                self.root.after(0, lambda: messagebox.showerror("FFmpeg error", str(e)))
        threading.Thread(target=work, daemon=True).start()


if __name__ == "__main__":
    root = TkinterDnD.Tk() if DND_AVAILABLE else tk.Tk()
    VideoToolApp(root)
    root.mainloop()
