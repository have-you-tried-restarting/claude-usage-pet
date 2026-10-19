# the settings window (sidebar, pages, search, keyboard control).
import datetime
import math
import time
import tkinter as tk
import tkinter.font as tkfont
import webbrowser

from .art import ARMS, BLOCK_H, BLOCK_W, BODY, BUBBLE, BUBBLE_TEXT, EYE, EYES, IDLE_C, LEGS_STAND, ORANGE, TRACK
from .dev import DEV_GROUPS
from .config import (IDLE_AFTER_MIN, IDLE_POLL_SECONDS, MAX_SCALE, MIN_SCALE, PANIC_CHOICES, POLL_CHOICES, PROFILE_NAMES, QUIET_FROM_CHOICES,
    QUIET_TO_CHOICES, BEDTIME_CHOICES, SHORTCUTS, VERSION, WARN_CHOICES, combo_parts, key_name)
from .sounds import SOUND_DIR, SOUND_GROUPS
from .storage import DEFAULTS
from .tips import TIPS
from .ui import Canvas, Tooltip, round_corners, round_rect
from .usage import fmt_day, fmt_time
from .winapi import u32


# ---- settings window (right-click > settings) ----

def hour_name(h):
    return "Midnight" if h == 0 else f"{h % 12 or 12} {'AM' if h < 12 else 'PM'}"


PERF_POINTS = 90   # 3 minutes of performance history, one point every 2 seconds
PROJECT_URL = "https://github.com/have-you-tried-restarting/claude-usage-pet"
ICON_FONT = "Segoe MDL2 Assets"   # windows' own icon font


class SettingsWindow:
    # laid out like the claude desktop app's settings: a sidebar of pages on the left (with search),
    # and on the right the page title, then sections as rounded cards: what a setting does on the left,
    # its control on the right. resizable, scrolls, and works from the keyboard too.
    BG, SIDE, CARD, LINE = "#262624", "#1f1e1d", "#30302e", "#3d3d3a"
    FG, DIM, FAINT = "#faf9f5", "#a6a39a", "#6b6a65"
    ON, KNOB, SEL, WELL = "#d97757", "#faf9f5", "#3d3c38", "#232321"
    CHIP_ON, CHIP_OFF = "#4a3128", "#3a3936"
    CAP, CAP_EDGE, WARN, GOOD, BAD = "#3d3c38", "#4d4c47", "#e8a33d", "#4caf7d", "#e5534b"
    FIX = "#6aa9ff"                          # what to do about an error (blue, like the details panel)
    W, H = 820, 580                          # starting size (base units, before display scaling)
    MIN_W, MIN_H, MAX_W = 800, 420, 1100     # the tallest it can go is the screen's height. (800 wide so the
                                             # diary's longest row, "Jumps to windows   9,999 made · 9,999 missed",
                                             # fits in its column without the words running into the numbers)
    SB, TOP = 196, 46                        # sidebar width, and the strip along the top
    PAGES = (("mascot", "Mascot", ""), ("appearance", "Appearance", ""),
             ("sound", "Sound & talking", ""), ("usage", "Usage & alerts", ""),
             ("shortcuts", "Shortcuts", ""), ("system", "System", ""),
             ("about", "About & stats", ""))
    DEV_PAGE = ("dev", "Developer", "\ue943")   # only in dev mode (ctrl + shift + D in here)

    def __init__(self, pet):
        self.pet, self.win, self.tab, self.fonts = pet, None, "mascot", {}
        self.hits, self.drag, self.move_from, self.s = [], None, None, 1.0
        self.tips, self.tooltip = [], None   # (x1, y1, x2, y2, text): options that explain themselves on hover
        self.recording, self.key_note = None, None   # which shortcut is waiting for keys / a message under it
        self.scroll, self.max_scroll, self.fixed_n = 0, 0, 0
        self.resizing, self.redraw_job, self.sized = None, None, False
        self.query, self.search = "", None
        self.focusables, self.focus_key, self.kb = [], None, False   # keyboard focus
        self.saved_until, self.saved_job, self.saved_label = 0.0, None, "Saved"
        self.dev_job, self.dev_seen = None, None   # (the dev page keeps itself up to date)

    def pages(self):
        return self.PAGES + ((self.DEV_PAGE,) if self.pet.dev_on else ())

    # ---- what's on each page ----
    def sections(self, page):
        # each section: a heading, its rows, which settings its "Reset" puts back, and when it shows at all
        p = self.pet
        sounds_on = lambda: bool(p.sounds.get())

        def row(kind, label, key=None, var=None, cmd=None, extra=None, show=None, words=""):
            return {"kind": kind, "label": label, "key": key, "var": var, "cmd": cmd, "extra": extra,
                    "show": show, "words": words}

        if page == "mascot":
            return [("Movement", ["energy"], [
                        row("choice", "Personality", "energy", p.energy, p.energy_changed, PROFILE_NAMES,
                            words="parkour lively normal chill statue move walk jump")]),
                    ("Behaviour", ["naps", "wizard", "apprentices", "platforms", "rare", "anim"], [
                        row("toggle", "Take naps", "naps", p.naps, p.naps_changed, words="sleep"),
                        row("toggle", "Wizard when Claude works", "wizard", p.wizard, p.changed,
                            words="hat magic tome book reading"),
                        row("toggle", "Apprentices for parallel sessions", "apprentices", p.apprentices, p.changed,
                            show=lambda: bool(p.wizard.get()), words="helpers sessions wizard"),
                        row("toggle", "Stand on windows", "platforms", p.platforms, p.changed, words="jump ledge"),
                        row("toggle", "Rare surprises", "rare", p.rare, p.changed, words="ufo cat shiny alien"),
                        row("toggle", "Animations", "anim", p.anim, p.anim_changed, words="still motion")])]
        if page == "appearance":
            return [("Preview", None, [row("preview", "Preview", words="look size bubble")]),
                    ("Mascot", ["scale", "seasonal", "bedtime", "bedtime_at"], [
                        row("slider", "Size", "scale", p.size_var, p.set_scale, (MIN_SCALE, MAX_SCALE, 0.05, "{:.2f}x"),
                            words="big small scale"),
                        row("toggle", "Seasonal outfits", "seasonal", p.seasonal, p.changed,
                            words="halloween christmas hat pumpkin holiday"),
                        row("toggle", "Pajamas at bedtime", "bedtime", p.bedtime, p.changed,
                            words="night cap nightcap candle sleep pyjamas"),
                        row("choice", "Bedtime from", "bedtime_at", p.bedtime_at, p.changed,
                            [(v, hour_name(v)) for v in BEDTIME_CHOICES], show=lambda: bool(p.bedtime.get()),
                            words="night time hour")]),
                    ("Usage bubble", ["bubble", "bubble_style"], [
                        row("choice", "Bubble shows", "bubble", p.bubble_mode, p.changed,
                            (("all", "Limits + context"), ("both", "Both limits"), ("5h", "5-hour only"), ("hover", "On hover"))),
                        row("choice", "Bubble style", "bubble_style", p.bubble_style, p.changed,
                            (("numbers", "Numbers"), ("bars", "Bars"))),
                        row("toggle", "Keep details open", None, p.pin_var, p.pin_changed, words="panel pin")]),
                    ("Time and date", ["clock", "dates"], [
                        row("choice", "Clock", "clock", p.clock_fmt, p.clock_changed, (("12h", "3:05 PM"), ("24h", "15:05")),
                            words="12 24 hour am pm"),
                        row("choice", "Dates", "dates", p.dates, p.clock_changed,
                            (("ddmm", "Fri 16/10"), ("mmdd", "Fri 10/16")), words="day month")])]
        if page == "sound":
            return [("Sound effects", ["sounds", "volume"], [
                        row("toggle", "Sound effects", "sounds", p.sounds, p.sounds_changed, words="mute audio"),
                        row("slider", "Volume", "volume", p.volume, None, (0, 100, 5, "{:.0f}%"), show=sounds_on,
                            words="loud quiet")]),
                    ("Which sounds", ["muted"], [
                        row("sounds", "Which sounds", extra=SOUND_GROUPS, show=sounds_on,
                            words="poke bounce scream splat parachute eagle hay wizard magic dance music milestones")]),
                    ("Talking", ["chatter"], [
                        row("choice", "Chatter", "chatter", p.chatter, p.chatter_changed,
                            (("off", "Off"), ("some", "Sometimes"), ("lots", "A lot"), ("max", "Non-stop")),
                            words="speech talk lines chatty")]),
                    ("Quiet", ["quiet_hours", "quiet_from", "quiet_to", "dnd"], [
                        row("toggle", "Quiet hours", "quiet_hours", p.quiet_hours, p.changed,
                            words="night mute silent sleep"),
                        row("choice", "Quiet from", "quiet_from", p.quiet_from, p.changed,
                            [(v, hour_name(v)) for v in QUIET_FROM_CHOICES], show=lambda: bool(p.quiet_hours.get())),
                        row("choice", "Quiet until", "quiet_to", p.quiet_to, p.changed,
                            [(v, hour_name(v)) for v in QUIET_TO_CHOICES], show=lambda: bool(p.quiet_hours.get())),
                        row("toggle", "Follow Do Not Disturb", "dnd", p.dnd, p.changed,
                            words="focus assist presentation mute meeting")])]
        if page == "usage":
            warn_on = lambda: bool(p.warn.get())
            return [("Checking", ["poll"], [
                        row("choice", "Refresh every", "poll", p.poll, p.poll_changed,
                            [(v, f"{v // 60} min") for v in POLL_CHOICES], words="update interval")]),
                    ("Warnings", ["warn", "warn_at", "panic_at", "pace_warn", "notify"], [
                        row("toggle", "Warn when nearly full", "warn", p.warn, p.changed, words="ring"),
                        row("choice", "Yellow ring from", "warn_at", p.warn_at, p.changed,
                            [(v, f"{v}%") for v in WARN_CHOICES], show=warn_on),
                        row("choice", "Red ring from", "panic_at", p.panic_at, p.changed,
                            [(v, f"{v}%") for v in PANIC_CHOICES], show=warn_on),
                        row("toggle", "Early pace warning", "pace_warn", p.pace_warn, p.changed,
                            words="forecast run out fast"),
                        row("toggle", "Desktop notifications", "notify", p.notify_on, p.changed, words="toast alert")]),
                    ("Claude Code", ["cc_app"], [
                        row("toggle", "Count tokens like the Claude app", "cc_app", p.cc_app, p.cc_changed,
                            words="tokens stats")])]
        if page == "shortcuts":
            return [("Keyboard shortcuts", ["hotkeys", "keys"], [
                        row("toggle", "Keyboard shortcuts", "hotkeys", p.hotkeys, p.hotkeys_changed, words="hotkey keys"),
                        row("keys", "Shortcuts", extra=SHORTCUTS, show=lambda: bool(p.hotkeys.get()),
                            words="hide show details panel ctrl alt")])]
        if page == "system":
            return [("Startup", None, [
                        row("toggle", "Start with Windows", None, p.startup_var, p.startup_changed, words="boot login")]),
                    ("Tray", ["tray"], [
                        row("toggle", "Tray icon", "tray", p.tray_on, p.changed, words="notification area clock")]),
                    ("Screens", ["hide_fs", "one_monitor"], [
                        row("toggle", "Hide during full screen", "hide_fs", p.hide_fs, p.hide_fs_changed,
                            words="video game"),
                        row("toggle", "Stay on one monitor", "one_monitor", p.one_monitor, p.changed,
                            words="display screen")])]
        if page == "dev":
            return ([("Every animation", None, [row("devall", "Play every animation", words="all test debug")])]
                    + [(group, None, [row("devanims", group, extra=items, words=" ".join(n for _, n in items))])
                       for group, items in DEV_GROUPS]
                    + [("Right now", None, [row("devinfo", "Dev mode", words="state debug leave exit")])])
        return [("Claude login", None, [row("login", "Claude login", words="account sign in expired token check")]),
                ("Pet diary", None, [row("diary", "Pet diary", words="stats pokes throws jumps dances log count")]),
                ("Performance", None, [row("perf", "Performance", words="cpu memory fps frame rate stats")]),
                ("About", None, [row("about", "About", words="version github project")])]

    # ---- opening and closing ----
    def open(self):
        if self.win is not None and self.win.winfo_exists():
            self.win.lift()
            return
        p = self.pet
        w = self.win = tk.Toplevel(p.root)
        w.overrideredirect(True)
        w.attributes("-topmost", True)
        w.configure(bg=self.BG)
        self.fonts = {}
        self.canvas = Canvas(w, bg=self.BG, highlightthickness=0, takefocus=0)
        self.canvas.pack()
        self.canvas.bind("<ButtonPress-1>", self.press)
        self.canvas.bind("<B1-Motion>", self.motion)
        self.canvas.bind("<ButtonRelease-1>", self.release)
        self.canvas.bind("<MouseWheel>", self.wheel)
        self.canvas.bind("<Motion>", self.hover_cursor)
        self.canvas.bind("<Leave>", lambda e: self.tooltip.hide())
        self.tooltip = Tooltip(w, self.CARD, self.FG, self.DIM, self.font)
        w.bind("<Escape>", self.escape)
        w.bind("<KeyPress>", self.key)
        w.protocol("WM_DELETE_WINDOW", lambda: None if self.recording else self.close())   # alt + F4 while recording
        self.s = p.dpi
        # the search box is a real text box, sat on the canvas
        self.search_var = tk.StringVar()
        self.search = tk.Entry(self.canvas, textvariable=self.search_var, bg=self.WELL, fg=self.FG, relief="flat",
                               insertbackground=self.FG, highlightthickness=0, borderwidth=0,
                               font=self.font(8.5), takefocus=1)
        self.search_var.trace_add("write", lambda *a: self.searched())
        self.search.bind("<FocusIn>", self.search_in)
        self.search.bind("<FocusOut>", self.search_out)
        self.placeholder = False
        self.search_out()
        sc = p.screens[p.si]
        if p.settings_size and not self.sized:   # the size you left it at last time
            self.W, self.H = p.settings_size
        self.sized = True
        self.fit_to(sc)
        self.draw()
        pw, ph = self.size
        x = min(max(sc.wl + 10, round(p.x - pw / 2)), sc.wr - pw - 10)
        y = max(sc.wt + 10, sc.wb - ph - round(150 * self.s))
        w.geometry(f"{pw}x{ph}+{x}+{y}")
        round_corners(w)
        w.focus_force()

    def close(self):
        self.stop_recording()
        self.key_note = None
        if self.win is not None:
            self.tooltip.hide()
            if self.dev_job:
                self.win.after_cancel(self.dev_job)
                self.dev_job = None
            self.win.destroy()
            self.win = None

    def fit_to(self, sc):
        # keeps the size between the limits, and no taller than the screen
        max_h = max(self.MIN_H, int((sc.wb - sc.wt) / self.s) - 20)
        self.W = min(self.MAX_W, max(self.MIN_W, int(self.W)))
        self.H = min(max_h, max(self.MIN_H, int(self.H)))

    # ---- drawing helpers. positions are in base units, times s on screen. ----
    def font(self, size, bold=False, family="Segoe UI"):
        px = max(8, round(size * 4 / 3 * self.s))
        key = (px, bold, family)
        if key not in self.fonts:
            self.fonts[key] = tkfont.Font(root=self.win, family=family, size=-px, weight="bold" if bold else "normal")
        return self.fonts[key]

    def px_font(self, px):
        # a bold font at an exact pixel size (the preview draws at the mascot's real size)
        if ("px", px) not in self.fonts:
            self.fonts[("px", px)] = tkfont.Font(root=self.win, family="Segoe UI", size=-px, weight="bold")
        return self.fonts[("px", px)]

    def text(self, x, y, text, fill, size, bold=False, anchor="nw", width=None, family="Segoe UI"):
        kw = {"width": width * self.s} if width else {}
        item = self.canvas.create_text(x * self.s, y * self.s, anchor=anchor, fill=fill,
                                       font=self.font(size, bold, family), text=text, **kw)
        return self.canvas.bbox(item)[3] / self.s

    def box(self, x0, y0, x1, y1, r, fill, bg=None, tag=""):
        s = self.s
        round_rect(self.canvas, x0 * s, y0 * s, x1 * s, y1 * s, r * s, fill, bg or self.BG, True, tag)

    def hit(self, what, x0, y0, x1, y1, focus=None):
        # a clickable area. focus = (key, on space/enter, on left/right) makes it reachable with tab too.
        s = self.s
        self.hits.append((what, x0 * s, y0 * s, x1 * s, y1 * s))
        if focus:
            self.focusables.append((focus[0], (x0, y0, x1, y1), focus[1], focus[2] if len(focus) > 2 else None))

    def changed_saved(self, label="Saved"):
        # the little "saved" note in the corner after each change
        self.saved_until, self.saved_label = time.time() + 1.6, label
        if self.saved_job:
            self.win.after_cancel(self.saved_job)
        self.saved_job = self.win.after(1700, lambda: (setattr(self, "saved_job", None),
                                                      self.win is not None and self.draw()))

    # ---- the whole window ----
    def draw(self):
        s, W, H, c = self.s, self.W, self.H, self.canvas
        view = H - self.TOP
        for _ in range(2):   # (twice at most: once more if the scroll had to be pulled back in)
            c.delete("all")
            self.hits, self.focusables, self.tips = [], [], []
            end = self.draw_content(self.SB + 28, W - 28, self.TOP + 4 - self.scroll)
            self.max_scroll = max(0, round(end + self.scroll - self.TOP - 4 - view + 24))
            if self.scroll <= self.max_scroll:
                break
            self.scroll = self.max_scroll
        content = [h for h in self.hits if h[4] > self.TOP * s and h[2] < H * s and h[1] >= self.SB * s]
        content_focus = self.focusables
        self.hits, self.focusables = [], []
        # the strip along the top of the content (scrolled content slides under it), with the close button
        c.create_rectangle(self.SB * s, 0, W * s, self.TOP * s, fill=self.BG, outline="")
        if self.scroll > 0:
            c.create_line(self.SB * s, self.TOP * s - 1, W * s, self.TOP * s - 1, fill=self.LINE)
        self.hits.append((("move",), self.SB * s, 0, (W - 40) * s, self.TOP * s))
        self.text(W - 22, 22, "", self.DIM, 8, family=ICON_FONT, anchor="center")
        self.hit(("close",), W - 40, 4, W - 4, 40)
        self.draw_sidebar()
        # a slim scrollbar, the resize grip, and the "saved" note
        if self.max_scroll:
            track = view - 16
            bar = max(24, track * view / (view + self.max_scroll))
            by = self.TOP + 8 + (track - bar) * self.scroll / self.max_scroll
            self.box(W - 7, by, W - 3, by + bar, 2, self.LINE)
        for i in range(3):   # three little diagonal rows of dots: drag me
            for j in range(i + 1):
                gx, gy = W - 7 - (i - j) * 4, H - 7 - j * 4
                c.create_rectangle((gx - 1) * s, (gy - 1) * s, (gx + 1) * s, (gy + 1) * s, fill=self.FAINT, outline="")
        self.hits += [(("resize", 1, 1), (W - 16) * s, (H - 16) * s, W * s, H * s),
                      (("resize", 1, 0), (W - 5) * s, self.TOP * s, W * s, H * s),
                      (("resize", 0, 1), self.SB * s, (H - 5) * s, W * s, H * s)]
        if time.time() < self.saved_until:
            label = f"✓  {self.saved_label}"
            w = self.font(8, True).measure(label) / s + 24
            self.box(W - 24 - w, H - 44, W - 24, H - 18, 8, self.SEL)
            self.text(W - 24 - w / 2, H - 31, label, self.GOOD, 8, True, "center")
        self.fixed_n = len(self.hits)
        self.hits += content
        self.focusables = self.focusables + [f for f in content_focus]
        if self.kb:   # the keyboard focus ring
            ring = next((f for f in self.focusables if f[0] == self.focus_key), None)
            if ring:
                x0, y0, x1, y1 = ring[1]
                c.create_rectangle((x0 - 3) * s, (y0 - 3) * s, (x1 + 3) * s, (y1 + 3) * s, outline=self.ON,
                                   width=max(1, round(1.5 * s)))
        self.size = (round(W * s), round(H * s))
        self.canvas.configure(width=self.size[0], height=self.size[1])
        if self.tab == "dev" and not self.query and self.dev_job is None:
            self.dev_job = self.win.after(250, self.dev_watch)

    def draw_sidebar(self):
        s, c, H = self.s, self.canvas, self.H
        c.create_rectangle(0, 0, self.SB * s, H * s, fill=self.SIDE, outline="")
        self.hits.append((("move",), 0, 0, self.SB * s, 40 * s))
        self.text(20, 15, "Settings", self.FG, 11, True)
        # search
        x0, y0, x1, y1 = 14, 48, self.SB - 14, 76
        focused = self.win is not None and self.win.focus_get() is self.search
        if focused:
            self.box(x0 - 1.5, y0 - 1.5, x1 + 1.5, y1 + 1.5, 9, self.ON, self.SIDE)
        self.box(x0, y0, x1, y1, 8, self.WELL, self.ON if focused else self.SIDE)
        self.text(x0 + 15, (y0 + y1) / 2, "", self.FAINT, 7.5, family=ICON_FONT, anchor="center")
        c.create_window((x0 + 27) * s, (y0 + 5) * s, anchor="nw", window=self.search,
                        width=(x1 - x0 - 34) * s, height=(y1 - y0 - 10) * s)
        # pages
        y = 92
        for name, label, icon in self.pages():
            on = self.tab == name and not self.query
            if on:
                self.box(10, y, self.SB - 10, y + 32, 8, self.SEL, self.SIDE)
            self.text(28, y + 16, icon, self.FG if on else self.DIM, 9, family=ICON_FONT, anchor="center")
            self.text(46, y + 16, label, self.FG if on else self.DIM, 9, on, anchor="w")
            self.hit(("tab", name), 10, y, self.SB - 10, y + 32, (("nav", name), lambda n=name: self.go(n)))
            y += 36

    def draw_content(self, x0, x1, y):
        # the page title, then each section as a heading and a card
        if self.query:
            return self.draw_results(x0, x1, y)
        title = next(label for name, label, _ in self.pages() if name == self.tab)
        y = self.text(x0, y + 6, title, self.FG, 15, True) + 18
        for heading, reset, rows in self.sections(self.tab):
            rows = [r for r in rows if not r["show"] or r["show"]()]
            if rows:
                y = self.section(x0, x1, y, heading, reset, rows)
        return y

    def section(self, x0, x1, y, heading, reset, rows, heading_text=None):
        # a small heading (and a "Reset" on the right), then the rows in one rounded card
        self.text(x0 + 2, y, heading_text or heading, self.DIM, 8, True)
        if reset:
            w = self.font(7.5).measure("Reset") / self.s
            self.text(x1 - 2, y + 1, "Reset", self.FAINT, 7.5, anchor="ne")
            self.hit(("reset", tuple(reset)), x1 - w - 8, y - 2, x1 + 2, y + 16,
                     (("reset", heading), lambda r=tuple(reset): self.reset_section(r)))
        y += 22
        tag = f"card{y:.0f}"
        top = y
        for i, r in enumerate(rows):
            if i:
                self.canvas.create_line((x0 + 16) * self.s, y * self.s, (x1 - 16) * self.s, y * self.s, fill=self.LINE)
            y = self.draw_row(x0, x1, y, r)
        self.box(x0, top, x1, y, 10, self.CARD, tag=tag)
        self.canvas.tag_lower(tag)
        return y + 24

    # ---- one row of settings ----
    def draw_row(self, x0, x1, y, r):
        p, s = self.pet, self.s
        kind, label, var, cmd, extra = r["kind"], r["label"], r["var"], r["cmd"], r["extra"]
        desc = TIPS.get(label, ("",))[0]
        lx, inner = x0 + 16, x1 - x0 - 32
        top = y + 14
        if kind == "toggle":
            self.text(lx, top, label, self.FG, 9)
            end = self.text(lx, top + 19, desc, self.DIM, 8, width=inner - 60) if desc else top + 17
            on = bool(var.get())
            self.switch(x1 - 16, top, on)
            act = lambda v=var, c=cmd: self.flip(v, c)
            self.hit(("toggle", var, cmd), x0, y, x1, end + 14, (("row", label), act))
            return end + 14
        if kind == "choice":
            seg_w = self.segment_width(extra)
            beside = seg_w <= inner * 0.5
            self.text(lx, top, label, self.FG, 9)
            end = self.text(lx, top + 19, desc, self.DIM, 8, width=inner - (seg_w + 20 if beside else 0)) \
                if desc else top + 17
            if beside:
                self.segmented(x1 - 16 - seg_w, top - 4, extra, var, cmd, label)
                return max(end, top + 26) + 14
            self.segmented(lx, end + 10, extra, var, cmd, label)
            return end + 10 + 28 + 14
        if kind == "slider":
            lo, hi, step, fmt = extra
            self.text(lx, top, label, self.FG, 9)
            self.text(x1 - 16, top, fmt.format(var.get()), self.DIM, 9, True, "ne")
            end = self.text(lx, top + 19, desc, self.DIM, 8, width=inner) if desc else top + 17
            sx0, sx1, ty = lx, x1 - 16, end + 16
            frac = (float(var.get()) - lo) / (hi - lo)
            self.box(sx0, ty - 2, sx1, ty + 2, 2, self.LINE, self.CARD)
            self.box(sx0, ty - 2, max(sx0 + 4, sx0 + (sx1 - sx0) * frac), ty + 2, 2, self.ON, self.CARD)
            kx = sx0 + (sx1 - sx0) * frac
            self.box(kx - 8, ty - 8, kx + 8, ty + 8, 8, self.KNOB, self.CARD)

            def nudge(d, v=var, c=cmd, lo=lo, hi=hi, step=step):
                nv = min(hi, max(lo, round((float(v.get()) + d * step) / step) * step))
                nv = round(nv, 2) if isinstance(v, tk.DoubleVar) else int(nv)
                v.set(nv)
                if c:
                    c(nv)
                if v is p.volume:
                    p.volume_changed()
                self.changed_saved()

            self.hit(("slide", var, cmd, lo, hi, step, sx0, sx1), x0, ty - 12, x1, ty + 12,
                     (("row", label), None, nudge))
            return ty + 10 + 14
        if kind == "preview":
            return self.draw_preview(x0, x1, y)
        if kind == "sounds":
            return self.draw_sounds(x0, x1, y, extra)
        if kind == "keys":
            return self.draw_keys(x0, x1, y, extra)
        if kind == "login":
            return self.draw_login(x0, x1, y)
        if kind == "perf":
            return self.draw_perf(x0, x1, y)
        if kind == "diary":
            return self.draw_diary(x0, x1, y)
        if kind == "devall":
            return self.draw_dev_all(x0, x1, y)
        if kind == "devanims":
            return self.draw_dev_anims(x0, x1, y, extra)
        if kind == "devinfo":
            return self.draw_dev_info(x0, x1, y)
        return self.draw_about(x0, x1, y)

    def switch(self, right, y, on):
        sw, sh = 36, 20
        sx = right - sw
        self.box(sx, y, sx + sw, y + sh, sh / 2, self.ON if on else self.LINE, self.CARD)
        kx = sx + sw - sh + 3 if on else sx + 3
        self.box(kx, y + 3, kx + sh - 6, y + sh - 3, (sh - 6) / 2, self.KNOB, self.ON if on else self.LINE)

    def segment_width(self, options):
        f = self.font(8, True)
        return sum(f.measure(t) / self.s + 20 for _, t in options) + 6

    def segmented(self, x, y, options, var, cmd, label):
        # a row of options in one rounded well; the chosen one sits on a lighter tab (like claude's)
        f = self.font(8, True)
        w = self.segment_width(options)
        self.box(x, y, x + w, y + 28, 8, self.WELL, self.CARD)
        cx = x + 3
        values = [v for v, _ in options]
        explain = dict(TIPS.get(label, ("", []))[1])   # (each option's explanation, shown when you hover it)
        for value, t in options:
            ow = f.measure(t) / self.s + 20
            on = var.get() == value
            if on:
                self.box(cx, y + 3, cx + ow, y + 25, 6, self.SEL, self.WELL)
            self.text(cx + ow / 2, y + 14, t, self.FG if on else self.DIM, 8, True, "center")
            self.hits.append((("pick", var, value, cmd), cx * self.s, y * self.s, (cx + ow) * self.s, (y + 28) * self.s))
            if t in explain:
                self.tips.append((cx * self.s, y * self.s, (cx + ow) * self.s, (y + 28) * self.s, f"{t}: {explain[t]}"))
            cx += ow

        def step(d, var=var, cmd=cmd, values=values):
            i = values.index(var.get()) if var.get() in values else 0
            var.set(values[(i + d) % len(values)])
            cmd()
            self.changed_saved()

        self.focusables.append((("row", label), (x, y, x + w, y + 28), lambda: step(1), step))

    # ---- the special rows ----
    def draw_preview(self, x0, x1, y):
        # a small live picture of the mascot at the chosen size, with its usage bubble
        p, s, c = self.pet, self.s, self.canvas
        sc = p.scale
        bw, bh = max(1, round(BLOCK_W * sc)), max(2, round(BLOCK_H * sc))   # real pixels, like on screen
        pet_w, pet_h = 18 * bw, 5 * bh
        area_h = (pet_h + 60 * sc + 50) / s
        ax0, ay0, ax1, ay1 = x0 + 16, y + 14, x1 - 16, y + 14 + area_h
        self.box(ax0, ay0, ax1, ay1, 8, self.WELL, self.CARD)
        mid, base = (ax0 + ax1) / 2 * s, (ay1 - 16) * s
        px, py = mid - pet_w / 2, base - pet_h
        for row_i, line in enumerate(BODY):
            a, b = line.index("#"), line.rindex("#") + 1
            c.create_rectangle(px + a * bw, py + row_i * bh, px + b * bw, py + (row_i + 1) * bh, fill=ORANGE, outline="")
        for col, row_i in ARMS:
            c.create_rectangle(px + col * bw, py + row_i * bh, px + (col + 1) * bw, py + (row_i + 1) * bh, fill=ORANGE,
                               outline="")
        for col in LEGS_STAND:
            c.create_rectangle(px + col * bw, py + 4 * bh, px + (col + 1) * bw, py + 5 * bh, fill=ORANGE, outline="")
        for col in EYES:
            c.create_rectangle(px + col * bw, py + bh, px + (col + 1) * bw, py + 2 * bh, fill=EYE, outline="")
        # the bubble, as it'd look
        f = self.px_font(max(8, round(11 * sc)))
        pad, dot = round(7 * sc), max(4, round(6 * sc))
        bars = p.bubble_bars() if p.bubble_style.get() == "bars" and p.data else None
        if bars:
            lf = self.px_font(max(8, round(10 * sc)))
            lab_w = max(lf.measure(lab) for lab, _, _ in bars)
            bar_w, bar_h, row_h = round(56 * sc), max(3, round(5 * sc)), lf.metrics("linespace")
            bub_w, bub_h = 2 * pad + lab_w + round(6 * sc) + bar_w, len(bars) * row_h + round(6 * sc)
        else:
            segs = p.bubble_segments()
            bub_w = 2 * pad + sum(dot + round(4 * sc) + f.measure(t_) for t_, _ in segs) + round(9 * sc) * (len(segs) - 1)
            bub_h = f.metrics("linespace") + round(6 * sc)
        bx, by = mid - bub_w / 2, py - round(6 * sc) - bub_h
        round_rect(c, bx, by, bx + bub_w, by + bub_h, round(5 * sc), BUBBLE, self.WELL, True)
        c.create_polygon(mid - round(4 * sc), by + bub_h - 1, mid + round(4 * sc), by + bub_h - 1, mid,
                         by + bub_h + round(4 * sc), fill=BUBBLE, outline="")
        if bars:
            yy = by + round(3 * sc)
            for lab, pct, color in bars:
                ym = yy + row_h / 2
                c.create_text(bx + pad, ym, anchor="w", text=lab, fill=BUBBLE_TEXT, font=lf)
                xb = bx + pad + lab_w + round(6 * sc)
                c.create_rectangle(xb, ym - bar_h / 2, xb + bar_w, ym + bar_h / 2, fill=TRACK, outline="")
                c.create_rectangle(xb, ym - bar_h / 2, xb + bar_w * min(pct, 100) / 100, ym + bar_h / 2, fill=color,
                                   outline="")
                yy += row_h
        else:
            xx, ym = bx + pad, by + bub_h / 2
            for i, (t_, color) in enumerate(segs):
                if i:
                    xx += round(9 * sc)
                c.create_oval(xx, ym - dot / 2, xx + dot, ym + dot / 2, fill=color, outline="")
                xx += dot + round(4 * sc)
                c.create_text(xx, ym, anchor="w", text=t_, fill=BUBBLE_TEXT, font=f)
                xx += f.measure(t_)
        note = {"hover": "The bubble only shows while you hover the mascot.",
                "5h": "Showing the 5-hour limit only.", "both": "Showing both limits, without the chat's context."}.get(p.bubble_mode.get(), "Live: changes here show straight away.")
        end = self.text(x0 + 16, ay1 + 8, note, self.DIM, 7.5, width=x1 - x0 - 32)
        return end + 14

    def draw_sounds(self, x0, x1, y, groups):
        # every sound as a chip: tap the name to switch it on or off, tap ▶ to hear it
        y = self.text(x0 + 16, y + 14, "Tap a sound to switch it on or off. Tap ▶ to hear it.", self.DIM, 8,
                      width=x1 - x0 - 32)
        for group, items in groups:
            y += 10
            self.text(x0 + 16, y, group.upper(), self.FAINT, 7, True)
            x, y = x0 + 16, y + 16
            for k, name in items:
                w = self.chip_width(name)
                if x + w > x1 - 16 and x > x0 + 16:
                    x, y = x0 + 16, y + 30
                self.chip(x, y, name, k)
                x += w + 6
            y += 24
        return y + 14

    def chip_width(self, label):
        return self.font(8, True).measure(label) / self.s + 30 + 24

    def chip(self, x, y, label, k):
        p, s, c = self.pet, self.s, self.canvas
        on = k not in p.muted
        w, h = self.chip_width(label), 24
        self.box(x, y, x + w, y + h, h / 2, self.CHIP_ON if on else self.CHIP_OFF, self.CARD)
        cx, cy, rad = x + 12, y + h / 2, 3.5
        if on:
            c.create_oval((cx - rad) * s, (cy - rad) * s, (cx + rad) * s, (cy + rad) * s, fill=self.ON, outline="")
        else:
            c.create_oval((cx - rad) * s, (cy - rad) * s, (cx + rad) * s, (cy + rad) * s, fill="", outline=self.FAINT,
                          width=max(1, round(1.2 * s)))
        self.text(x + 21, cy, label, self.FG if on else self.DIM, 8, True, "w")
        sep = x + w - 24
        c.create_line(sep * s, (y + 5) * s, sep * s, (y + h - 5) * s, fill=self.LINE)
        self.text(sep + 12, cy, "▶", self.DIM, 6.5, anchor="center")
        self.hits.append((("hear", k), sep * s, y * s, (x + w) * s, (y + h) * s))
        self.hit(("sound", k), x, y, sep, y + h,
                 (("chip", k), lambda k=k: self.toggle_chip(k), lambda d, k=k: p.play(k, preview=True)))

    def toggle_chip(self, k):
        self.pet.toggle_sound(k)
        self.changed_saved()

    def draw_keys(self, x0, x1, y, shortcuts):
        y = self.text(x0 + 16, y + 14, TIPS["Shortcuts"][0], self.DIM, 8, width=x1 - x0 - 32)
        for name, title, what in shortcuts:
            y += 14
            row = y
            self.text(x0 + 16, y, title, self.FG, 9)
            y = self.text(x0 + 16, y + 18, what, self.DIM, 7.5, width=x1 - x0 - 32 - 170)
            self.keycaps(x1 - 16, row - 2, name)
            note = self.key_note if self.key_note and self.key_note[0] == name else None
            if not note and self.recording != name and self.pet.binds.get(name) \
                    and self.pet.bind_ok.get(name) is False:
                note = (name, "Another app already uses these keys. Pick different ones.")
            if note:
                y = self.text(x0 + 16, y + 4, note[1], self.WARN, 7.5, width=x1 - x0 - 32)
            self.hit(("bind", name), x0, row - 6, x1, y + 6, (("bind", name), lambda n=name: self.toggle_record(n)))
        return y + 16

    def keycaps(self, right, y, name):
        # the keys of one shortcut, right-aligned: [Ctrl] [Alt] [P]. while recording: an orange "press keys" box.
        s = self.s
        f8 = self.font(8, True)
        if self.recording == name:
            label = "Press the new keys…"
            w = f8.measure(label) / s + 24
            self.box(right - w, y, right, y + 24, 6, self.ON, self.CARD)
            self.box(right - w + 1.5, y + 1.5, right - 1.5, y + 22.5, 5, self.CARD, self.ON)
            self.text(right - w / 2, y + 12, label, self.ON, 8, True, "center")
            return
        combo = self.pet.binds.get(name)
        if not combo:
            self.text(right - 4, y + 12, "Not set — click to add", self.FAINT, 8, True, "e")
            return
        x = right
        for part in reversed(combo_parts(combo)):
            w = f8.measure(part) / s + 16
            x -= w
            # a key cap: a slightly lighter base under the face, so it looks like it sticks up
            self.box(x, y, x + w, y + 24, 5, self.CAP_EDGE, self.CARD)
            self.box(x, y, x + w, y + 21.5, 5, self.CAP, self.CAP_EDGE)
            self.text(x + w / 2, y + 11, part, self.FG, 8, True, "center")
            x -= 4

    def draw_login(self, x0, x1, y):
        # is the pet logged in? and if not, exactly how to fix it
        p = self.pet
        err = p.error or ""
        if err.startswith(("login expired", "login refused", "access denied", "no login")):
            head = next(h for start, h in (("no login", "Not logged in"), ("login expired", "Login expired"),
                        ("login refused", "Login refused"), ("access denied", "Access denied")) if err.startswith(start))
            dot = self.BAD
        elif err.startswith("rate limited"):
            dot, head = self.WARN, "Rate limited"
        elif err:   # what went wrong, from the message's first sentence (the line under it says why)
            first = err.partition("\n\n")[0].split(". ", 1)[0]
            dot, head = self.WARN, first[0].upper() + first[1:]
        elif p.data:
            dot, head = self.GOOD, "Connected"
        else:
            dot, head = self.FAINT, "Checking…"
        cy = y + 22
        self.canvas.create_oval((x0 + 16) * self.s, (cy - 4) * self.s, (x0 + 24) * self.s, (cy + 4) * self.s,
                                fill=dot, outline="")
        self.text(x0 + 32, cy, head, self.FG, 9, True, "w")
        wait = max(0, math.ceil(p.next_at - time.time()))
        line = (f"Last checked {fmt_time(p.updated)}. " if p.updated else "") + \
               ("Checking now…" if p.busy else f"Next check in {wait // 60}m {wait % 60:02d}s.")
        end = self.text(x0 + 16, y + 38, line, self.DIM, 8, width=x1 - x0 - 140)
        if p.idle() and not err:
            end = self.text(x0 + 16, end + 4, f"Idle: nothing has used Claude for {IDLE_AFTER_MIN} minutes, so it "
                            f"checks every {IDLE_POLL_SECONDS // 60} minutes. Back to normal as soon as you use "
                            "Claude again.", IDLE_C, 8, width=x1 - x0 - 32)
        # a "check now" button
        label = "Check now"
        bw_ = self.font(8, True).measure(label) / self.s + 24
        self.box(x1 - 16 - bw_, y + 10, x1 - 16, y + 36, 7, self.SEL, self.CARD)
        self.text(x1 - 16 - bw_ / 2, y + 23, label, self.FG, 8, True, "center")
        self.hit(("check",), x1 - 16 - bw_, y + 10, x1 - 16, y + 36, (("check",), self.check_now))
        if err:
            head_, _, steps = err.partition("\n\n")
            why = head_.split(". ", 1)[1] if ". " in head_ else head_   # (the status line already says what's wrong)
            end = self.text(x0 + 16, end + 10, why[0].upper() + why[1:], self.DIM, 8, width=x1 - x0 - 32)
            if steps:
                end = self.text(x0 + 16, end + 8, steps, self.FIX, 8, width=x1 - x0 - 32)
        return end + 14

    def check_now(self):
        if time.time() >= self.pet.blocked_until:   # (not while the service told us to wait)
            self.pet.next_at = time.time()
        self.pet.refresh("manual")
        self.draw()

    def draw_perf(self, x0, x1, y):
        # live numbers about the pet itself, refreshed every 2 seconds while this page is open
        p, s, c = self.pet, self.s, self.canvas
        y = self.text(x0 + 16, y + 14, "How much of your computer the mascot uses. Updates every 2 seconds.",
                      self.DIM, 8, width=x1 - x0 - 32) + 6
        hist = list(p.perf_hist)
        rows = self.perf_rows()
        for i, (name, value, note, level, graph) in enumerate(rows):
            if i:
                c.create_line((x0 + 16) * s, y * s, (x1 - 16) * s, y * s, fill=self.LINE)
            y += 12
            dot = {0: self.GOOD, 1: self.WARN, 2: self.BAD}.get(level)
            if dot:
                c.create_oval((x0 + 16) * s, (y + 4) * s, (x0 + 23) * s, (y + 11) * s, fill=dot, outline="")
            self.text(x0 + (29 if dot else 16), y, name, self.FG, 8.5, True)
            self.text(x1 - 16, y, value, self.FG, 9, True, "ne")
            y = self.text(x0 + 16, y + 17, note, self.DIM, 7.5, width=x1 - x0 - 32 - 100)
            if graph is not None:
                self.graph(x0 + 16, y + 6, x1 - 16, y + 52, [h[graph[0]] for h in hist], *graph[1:])
                self.text(x0 + 16, y + 55, "3 min ago", self.FAINT, 7)
                y = self.text(x1 - 16, y + 55, "now", self.FAINT, 7, anchor="ne")
            y += 12
        return y + 4

    def perf_rows(self):
        # (name, value, small note, 0 good / 1 so-so / 2 high / None no rating, graph or None)
        p = self.pet
        pf = p.perf
        up = int(time.time() - p.started)
        h, m = divmod(up // 60, 60)
        moving = p.frame_ms() <= 16
        try:
            disk = sum(f.stat().st_size for f in SOUND_DIR.glob("*.wav")) / 2 ** 20
        except OSError:
            disk = 0.0
        cpu = pf["cpu"]
        # graph = (which value in the history, unit, smallest top of the scale, line colour, fill colour)
        return [
            ("CPU", f"{cpu:.1f}%", f"of your whole processor ({pf.get('cpu_core', 0):.1f}% of one core)",
             0 if cpu < 1 else 1 if cpu < 3 else 2, (0, "%", 1, "#d97757", "#3d2b24")),
            ("Memory", f"{pf['mem']:.0f} MB", "in use right now", 0 if pf["mem"] < 80 else 1 if pf["mem"] < 150 else 2,
             (1, " MB", 64, "#5ea1ff", "#25303f")),
            ("Frame rate", f"{pf['fps']:.0f} fps", "60 while moving, less while standing still" if moving else
             "slows down while standing still, to save power", None, (2, " fps", 60, "#4caf7d", "#24362c")),
            ("Usage checks", f"{p.checks_ok} ok · {p.checks_failed} failed",
             f"every {p.poll.get() // 60} min" + (f" · last at {fmt_time(p.updated)}" if p.updated else ""),
             0 if not p.checks_failed else 1, None),
            ("Claude Code logs", f"{getattr(p.cc, 'scan_ms', 0):.0f} ms", "to read new log lines (in the background)",
             None, None),
            ("Windows watched", f"{len(p.plats)}", "for standing on and bumping into", None, None),
            ("Sound files", f"{disk:.1f} MB", "made once and kept in your temp folder", None, None),
            ("Running for", f"{h}h {m}m" if h else f"{m}m", "since the mascot started", None, None),
        ]

    def graph(self, x0, y0, x1, y1, values, unit, floor, line, fill):
        # a small area chart: newest on the right, the last 3 minutes across. the scale grows to fit.
        s, c = self.s, self.canvas
        self.box(x0, y0, x1, y1, 6, self.WELL, self.CARD)
        top = max([floor] + [v * 1.2 for v in values])
        self.text(x0 + 6, y0 + 3, f"{top:.0f}{unit}" if top >= 10 else f"{top:.1f}{unit}", self.FAINT, 6.5)
        if len(values) < 2:
            self.text((x0 + x1) / 2, (y0 + y1) / 2, "collecting…", self.FAINT, 7, anchor="center")
            return
        gx0, gx1, gy0, gy1 = x0 + 2, x1 - 2, y0 + 4, y1 - 2
        step = (gx1 - gx0) / (PERF_POINTS - 1)
        start = gx1 - step * (len(values) - 1)
        pts = [(start + i * step, gy1 - (gy1 - gy0) * min(v, top) / top) for i, v in enumerate(values)]
        area = [start * s, gy1 * s] + [v * s for xy in pts for v in xy] + [pts[-1][0] * s, gy1 * s]
        c.create_polygon(area, fill=fill, outline="")
        c.create_line([v * s for xy in pts for v in xy], fill=line, width=max(1, round(1.5 * s)))

    def draw_about(self, x0, x1, y):
        y = self.text(x0 + 16, y + 14, f"Claude usage pet {VERSION}", self.FG, 9, True)
        y = self.text(x0 + 16, y + 4, "A little desktop mascot that keeps an eye on your Claude plan usage. "
                      "Unofficial: not made by or affiliated with Anthropic.", self.DIM, 8, width=x1 - x0 - 32)
        label = "Star it on GitHub  ↗"
        w = self.font(8, True).measure(label) / self.s
        end = self.text(x0 + 16, y + 10, label, self.ON, 8, True)
        self.hit(("link",), x0 + 12, y + 6, x0 + 20 + w, end + 4, (("link",), lambda: webbrowser.open(PROJECT_URL)))
        label = "Show the tour again"
        w = self.font(8, True).measure(label) / self.s
        y = end + 6
        end = self.text(x0 + 16, y + 4, label, self.ON, 8, True)
        self.hit(("tour",), x0 + 12, y, x0 + 20 + w, end + 4, (("tour",), self.pet.restart_tour))
        return end + 14

    def draw_diary(self, x0, x1, y):
        # everything the mascot has been up to, two to a line
        p = self.pet
        log, st = p.log, p.cc_stats()
        n = lambda k: f"{int(log.get(k, 0)):,}"
        metres = log.get("walked", 0) * 0.0254 / 96   # screen pixels at 100% scaling, as real distance
        wiz = int(log.get("wizard_s", 0) // 60)
        since = ""
        if p.log_since:
            try:
                since = f" since {fmt_day(datetime.date.fromisoformat(p.log_since))}"
            except ValueError:
                pass
        items = [("Pokes", f"{p.pokes:,}"), ("Picked up", n("pickups")), ("Throws", n("throws")),
                 ("Little hops", n("hops")),
                 ("Jumps to windows", f"{n('leaps_made')} made · {n('leaps_missed')} missed"),
                 ("Leaps of faith", n("dives")), ("Water buckets", n("buckets")),
                 ("Bungee jumps", n("bungees")), ("Ziplines", n("ziplines")), ("Pole slides", n("poles")),
                 ("Web swings", n("webs")), ("Parachutes", n("chutes")),
                 ("Wall splats", n("splats")),
                 ("Monitor hops", n("trips")),
                 ("Dances", n("dances")), ("Naps", n("naps")), ("Games of fetch", n("fetches")),
                 ("Walked", f"{metres:,.0f} m" if metres < 1000 else f"{metres / 1000:,.2f} km"),
                 ("Time as a wizard", f"{wiz // 60}h {wiz % 60:02d}m" if wiz >= 60 else f"{wiz}m"),
                 ("Limits reset", n("resets")), ("5-hour at 100%", n("full_5h")), ("Weekly at 100%", n("full_week")),
                 ("Past-midnight sessions", f"{st['late']:,}" if st else "…"),
                 ("UFO abductions", n("ufo")), ("Cats met", n("cats")), ("Shiny days", n("shiny")),
                 ("Sweeps", n("sweeps")), ("Paintings", n("paintings")), ("Things fished out", n("catches")),
                 ("Balloons popped", n("balloons")), ("Paper planes", n("planes")), ("Coding jokes", n("gags")),
                 ("", "")]
        y = self.text(x0 + 16, y + 14, f"What the mascot's been up to{since}. Past-midnight sessions come from "
                      "Claude Code's logs (all time); the rest is counted by the mascot.", self.DIM, 8,
                      width=x1 - x0 - 32) + 8
        col_w = (x1 - x0 - 32 - 16) / 2
        for i, (label, value) in enumerate(items):
            cx = x0 + 16 + (i % 2) * (col_w + 16)
            ry = y + (i // 2) * 22
            self.text(cx, ry, label, self.DIM, 8)
            self.text(cx + col_w, ry, value, self.FG, 8, True, "ne")
        return y + (len(items) + 1) // 2 * 22 + 8

    # ---- the developer page (dev mode only) ----
    def pill(self, right, y, label, key, act):
        # a button, right-aligned
        w = self.font(8, True).measure(label) / self.s + 28
        self.box(right - w, y, right, y + 28, 8, self.ON, self.CARD)
        self.text(right - w / 2, y + 14, label, self.FG, 8, True, "center")
        self.hit(("do", act), right - w, y, right, y + 28, (("do", key), act))

    def draw_dev_all(self, x0, x1, y):
        p = self.pet
        now, prog = p.dev_status()
        busy = bool(now or p.dev_queue)
        top = y
        self.pill(x1 - 16, y + 12, "Stop" if busy else "Play all", "devall", self.dev_all)
        y = self.text(x0 + 16, y + 14, "Plays every animation below, one after another. Ones it can't do from where "
                      "it is get skipped. Nothing played here goes in the diary.", self.DIM, 8, width=x1 - x0 - 140)
        y = max(y, top + 40) - 8   # (not up against the button)
        if now or prog:
            line = f"Now: {now or '…'}" + (f"   ({prog[0]} of {prog[1]})" if prog else "")
            y = self.text(x0 + 16, y + 8, line, self.FG, 8.5, True)
        elif p.dev_note and p.dev_note[0] == "all":
            y = self.text(x0 + 16, y + 8, p.dev_note[1], self.GOOD, 8, width=x1 - x0 - 32)
        return y + 18

    def draw_dev_anims(self, x0, x1, y, items):
        # every animation in this group as a chip: tap one to play it now
        p, s = self.pet, self.s
        x, y = x0 + 16, y + 14
        f = self.font(8, True)
        for k, name in items:
            w = f.measure(name) / s + 34
            if x + w > x1 - 16 and x > x0 + 16:
                x, y = x0 + 16, y + 30
            on = p.dev_now == k or (k == "shiny" and p.shiny) or (k.startswith("look:") and p.dev_outfit == k[5:])
            self.box(x, y, x + w, y + 24, 12, self.CHIP_ON if on else self.CHIP_OFF, self.CARD)
            self.text(x + 13, y + 12, "▶", self.ON if on else self.DIM, 6.5, anchor="center")
            self.text(x + 22, y + 12, name, self.FG if on else self.DIM, 8, True, "w")
            act = lambda k=k: self.dev_play(k)
            self.hit(("do", act), x, y, x + w, y + 24, (("devchip", k), act))
            x += w + 6
        y += 24
        note = p.dev_note if p.dev_note and any(p.dev_note[0] == k for k, _ in items) else None
        if note:
            name = next(n for k, n in items if k == note[0])
            y = self.text(x0 + 16, y + 8, f"{name}: {note[1]}", self.WARN, 7.5, width=x1 - x0 - 32)
        return y + 16

    def draw_dev_info(self, x0, x1, y):
        # what it's up to, for checking things, and the way out
        p = self.pet
        where = ("in the air" if not p.grounded() else "on a window" if p.plat is not None else "on the taskbar")
        bits = [f"State: {p.state}" + (f" ({p.act})" if p.act else ""), where,
                f"screen {p.si + 1} of {len(p.screens)}"]
        if p.trip:
            bits.append(f"trip: {p.trip['how']} ({p.trip['stage'] or 'starting'})")
        y = self.text(x0 + 16, y + 14, "  ·  ".join(bits), self.FG, 8, width=x1 - x0 - 32)
        y = self.text(x0 + 16, y + 6, "Ctrl + Shift + D (with settings open) switches dev mode on and off.",
                      self.DIM, 8, width=x1 - x0 - 32)
        label = "Leave dev mode"
        w = self.font(8, True).measure(label) / self.s
        end = self.text(x0 + 16, y + 10, label, self.ON, 8, True)
        self.hit(("do", self.toggle_dev), x0 + 12, y + 6, x0 + 20 + w, end + 4, (("do", "leave"), self.toggle_dev))
        return end + 14

    def dev_play(self, key):
        self.pet.dev_play(key)
        self.draw()

    def dev_all(self):
        p = self.pet
        if p.dev_now or p.dev_queue:
            p.dev_stop()
        else:
            p.dev_play_all()
        self.draw()

    def toggle_dev(self):
        p = self.pet
        if p.dev_on:
            p.dev_leave()
            if self.tab == "dev":
                self.tab, self.scroll = "mascot", 0
        else:
            p.dev_on = True
            p.save()
            self.go("dev")
        self.changed_saved("Dev mode on" if p.dev_on else "Dev mode off")
        self.draw()

    def dev_watch(self):
        # while the dev page is open it redraws itself when the mascot's doing something new
        self.dev_job = None
        if self.win is None or self.tab != "dev" or self.query:
            return
        p = self.pet
        seen = (p.dev_status(), p.dev_note, p.state, p.act, p.trip and (p.trip["how"], p.trip["stage"]), p.si,
                p.plat is not None, p.grounded(), p.shiny, p.dev_outfit, bool(p.dev_queue))
        if seen != self.dev_seen and not (self.drag or self.resizing):
            self.dev_seen = seen
            self.draw()
        elif self.dev_job is None:
            self.dev_job = self.win.after(250, self.dev_watch)

    # ---- search ----
    def search_in(self, e=None):
        if self.placeholder:
            self.placeholder = False
            self.search.configure(fg=self.FG)
            self.search_var.set("")
        self.draw()

    def search_out(self, e=None):
        if not self.search_var.get().strip():
            self.placeholder = True
            self.search_var.set("Search settings")
            self.search.configure(fg=self.FAINT)
        if e is not None:
            self.draw()

    def searched(self):
        if self.placeholder:
            if self.search_var.get() == "Search settings":
                return
            self.placeholder = False   # real text arrived while the grey hint was showing
            self.search.configure(fg=self.FG)
        q = self.search_var.get().strip().lower()
        if q != self.query:
            self.query, self.scroll = q, 0
            self.draw()

    def draw_results(self, x0, x1, y):
        # every row, on any page, whose name, description or options mention what you typed
        q = self.query
        y = self.text(x0, y + 6, "Search", self.FG, 15, True) + 4
        y = self.text(x0, y, f"Results for “{self.search_var.get().strip()}”", self.DIM, 8.5) + 18
        found = 0
        for page, page_label, _ in self.pages():
            for heading, reset, rows in self.sections(page):
                hits = []
                for r in rows:
                    if r["show"] and not r["show"]():
                        continue
                    hay = " ".join([r["label"], TIPS.get(r["label"], ("",))[0], heading, page_label, r["words"]]
                                   + [str(t_) for _, t_ in (r["extra"] if r["kind"] == "choice" else [])]).lower()
                    if all(word in hay for word in q.split()):
                        hits.append(r)
                if hits:
                    found += len(hits)
                    y = self.section(x0, x1, y, heading, reset, hits, f"{page_label}  ›  {heading}")
        if not found:
            y = self.text(x0, y, "No settings match. Try a different word, like “sound” or “size”.",
                          self.DIM, 8.5, width=x1 - x0)
        return y

    # ---- doing things ----
    def go(self, page):
        self.stop_recording()
        self.key_note = None
        if self.query:
            self.search_var.set("")
            self.win.focus_set()
            self.search_out()
        self.tab, self.scroll = page, 0
        self.draw()

    def flip(self, var, cmd):
        var.set(not var.get())
        cmd()
        self.changed_saved()

    def toggle_record(self, name):
        if self.recording == name:
            self.stop_recording()   # clicked it again: never mind
        else:
            self.stop_recording()
            self.record(name)
        self.draw()

    def reset_section(self, keys):
        # puts one section's settings back to how they started
        p = self.pet
        for k in keys:
            if k == "muted":
                p.muted.clear()
            elif k == "keys":
                self.stop_recording()
                self.key_note = None
                p.reset_keys()
            elif k == "scale":
                p.set_scale(DEFAULTS["scale"])
            else:
                for page, _, _ in self.pages():
                    for _, _, rows in self.sections(page):
                        for r in rows:
                            if r["key"] == k and r["var"].get() != DEFAULTS[k]:
                                r["var"].set(DEFAULTS[k])
                                if r["cmd"]:
                                    r["cmd"]()
        p.save()
        self.changed_saved()
        self.draw()

    def hit_at(self, x, y):
        # over the sidebar or the top strip, only their own buttons count (not content scrolled under them)
        fixed_zone = y < self.TOP * self.s or x < self.SB * self.s
        hits = self.hits[:self.fixed_n] if fixed_zone else self.hits
        return next((h[0] for h in hits if h[1] <= x <= h[3] and h[2] <= y <= h[4]), None)

    def press(self, e):
        self.tooltip.hide()
        self.kb = False   # clicking hides the keyboard focus ring
        hit = self.hit_at(e.x, e.y)
        if self.win.focus_get() is self.search and (not hit or hit[0] != "search"):
            self.win.focus_set()
        if not hit:
            self.draw()
            return
        kind = hit[0]
        if kind == "close":
            self.close()
            return
        if kind == "move":
            self.move_from = (e.x_root - self.win.winfo_x(), e.y_root - self.win.winfo_y())
            return
        if kind == "resize":
            self.resizing = (hit[1], hit[2], e.x_root, e.y_root, self.W, self.H)
            return
        if kind == "search":
            self.draw()
            self.search.focus_set()
            return
        if kind == "tab":
            self.go(hit[1])
            return
        if kind == "toggle":
            self.flip(hit[1], hit[2])
        elif kind == "pick":
            if hit[1].get() != hit[2]:
                hit[1].set(hit[2])
                hit[3]()
                self.changed_saved()
        elif kind == "sound":
            self.toggle_chip(hit[1])
        elif kind == "hear":
            self.pet.play(hit[1], preview=True)
        elif kind == "bind":
            self.toggle_record(hit[1])
            return
        elif kind == "reset":
            self.reset_section(hit[1])
            return
        elif kind == "check":
            self.check_now()
            return
        elif kind == "link":
            webbrowser.open(PROJECT_URL)
        elif kind == "tour":
            self.pet.restart_tour()
        elif kind == "do":
            hit[1]()
            return
        elif kind == "slide":
            self.drag = hit
            self.slide_to(e.x)
            return
        if self.win is not None:
            self.draw()

    def motion(self, e):
        if self.resizing:
            dx_on, dy_on, x0, y0, w0, h0 = self.resizing
            self.W = w0 + (e.x_root - x0) / self.s if dx_on else self.W
            self.H = h0 + (e.y_root - y0) / self.s if dy_on else self.H
            self.fit_to(self.pet.screens[self.pet.si])
            if self.redraw_job is None:   # redraw at most about 60 times a second while dragging
                self.redraw_job = self.win.after(15, self.resized)
        elif self.drag:
            self.slide_to(e.x)
        elif self.move_from:
            self.win.geometry(f"+{e.x_root - self.move_from[0]}+{e.y_root - self.move_from[1]}")

    def resized(self):
        self.redraw_job = None
        if self.win is not None:
            self.draw()
            self.win.geometry(f"{self.size[0]}x{self.size[1]}")

    def release(self, e):
        if self.resizing:
            self.resizing = None
            self.pet.settings_size = [int(self.W), int(self.H)]   # remembered for next time
            self.pet.save()
        if self.drag:
            if self.drag[1] is self.pet.volume:
                self.pet.volume_changed()   # play a sample at the new volume
            self.changed_saved()
        self.drag = self.move_from = None

    def slide_to(self, x):
        _, var, cmd, lo, hi, step, x0, x1 = self.drag
        frac = min(1.0, max(0.0, (x / self.s - x0) / (x1 - x0)))
        v = round((lo + (hi - lo) * frac) / step) * step
        v = round(v, 2) if isinstance(var, tk.DoubleVar) else int(v)
        if v != var.get():
            var.set(v)
            if cmd:
                cmd(v)
            self.draw()

    def wheel(self, e):
        self.tooltip.hide()
        if self.max_scroll:
            self.scroll = min(self.max_scroll, max(0, self.scroll - e.delta / 120 * 48))
            self.draw()

    def hover_cursor(self, e):
        # resize arrows over the edges and corner, a hand over things you can click
        hit = self.hit_at(e.x, e.y)
        if hit and hit[0] == "resize":
            want = {(1, 1): "size_nw_se", (1, 0): "sb_h_double_arrow", (0, 1): "sb_v_double_arrow"}[hit[1:]]
        elif hit and hit[0] not in ("move",):
            want = "hand2"
        else:
            want = ""
        if self.canvas.cget("cursor") != want:
            self.canvas.configure(cursor=want)
        tip = next((t for x1, y1, x2, y2, t in self.tips if x1 <= e.x <= x2 and y1 <= e.y <= y2
                    and e.y > self.TOP * self.s), None)   # (not under the strip along the top)
        if tip:
            self.tooltip.show(tip, e.x_root, e.y_root, self.s)
        else:
            self.tooltip.hide()

    # ---- the keyboard ----
    def escape(self, e):
        if self.recording:   # esc cancels a shortcut you were typing
            self.stop_recording()
            self.key_note = None
            self.draw()
        elif self.query or self.win.focus_get() is self.search:     # ... or clears the search
            self.search_var.set("")
            self.win.focus_set()
            self.search_out()
        else:
            self.close()

    def move_focus(self, d):
        keys = [f[0] for f in self.focusables]
        if not keys:
            return
        i = keys.index(self.focus_key) if self.focus_key in keys else (-1 if d > 0 else 0)
        self.focus_key = keys[(i + d) % len(keys)]
        self.kb = True
        self.draw()
        ring = next(f for f in self.focusables if f[0] == self.focus_key)
        x0, y0, x1, y1 = ring[1]
        if ring[0][0] != "nav":   # scroll it into view
            if y0 < self.TOP + 8:
                self.scroll = max(0, self.scroll - (self.TOP + 8 - y0))
                self.draw()
            elif y1 > self.H - 16:
                self.scroll = min(self.max_scroll, self.scroll + (y1 - self.H + 16))
                self.draw()

    def key(self, e):
        # shortcuts being recorded first; then tab / arrows / space / enter to get around without a mouse
        if self.recording:
            return self.record_key(e)
        in_search = self.win.focus_get() is self.search
        ctrl = u32.GetAsyncKeyState(0x11) & 0x8000
        if ctrl and u32.GetAsyncKeyState(0x10) & 0x8000 and e.keysym.lower() == "d":   # (the hidden dev mode)
            self.toggle_dev()
            return "break"
        if ctrl and e.keysym.lower() == "f":
            self.search.focus_set()
            self.draw()
            return "break"
        if e.keysym in ("Tab", "ISO_Left_Tab"):
            if in_search:
                self.win.focus_set()
            self.move_focus(-1 if e.state & 0x1 else 1)
            return "break"
        if in_search:
            if e.keysym == "Down":
                self.win.focus_set()
                self.move_focus(1)
                return "break"
            return None   # typing in the search box
        if e.keysym in ("Down", "Up"):
            self.move_focus(1 if e.keysym == "Down" else -1)
            return "break"
        f = next((f for f in self.focusables if f[0] == self.focus_key), None) if self.kb else None
        if not f:
            return None
        if e.keysym in ("space", "Return") and f[2]:
            f[2]()
            self.draw()
            return "break"
        if e.keysym in ("Left", "Right") and f[3]:
            f[3](1 if e.keysym == "Right" else -1)
            self.draw()
            return "break"
        return None

    # ---- recording a new shortcut ----
    def record(self, name):
        self.recording, self.key_note = name, None
        self.pet.pause_keys(True)
        self.win.focus_force()

    def stop_recording(self):
        if self.recording:
            self.recording = None
            self.pet.pause_keys(False)

    def record_key(self, e):
        # the keys pressed while recording a shortcut. tk on windows gives the key's windows code as keycode.
        vk = e.keycode
        if vk in (0x10, 0x11, 0x12, 0x5B, 0x5C, 0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0x14, 0x90):
            return "break"   # just a modifier so far: wait for the real key
        down = lambda k: u32.GetAsyncKeyState(k) & 0x8000
        mods = ((2 if down(0x11) else 0) | (1 if down(0x12) else 0) | (4 if down(0x10) else 0)
                | (8 if down(0x5B) or down(0x5C) else 0))
        name = self.recording
        if vk == 0x08 and not mods:   # backspace: no shortcut for this one
            self.stop_recording()
            self.pet.set_key(name, None)
            self.changed_saved()
        elif key_name(vk) is None:
            self.key_note = (name, "That key can't be used. Try a letter, a number or an F key.")
        elif not mods & 0xB:
            self.key_note = (name, "Add Ctrl or Alt, so it doesn't get in the way of your typing.")
        else:
            combo = [mods, vk]
            other = next((title for n, title, _ in SHORTCUTS if n != name and self.pet.binds.get(n) == combo), None)
            if other:
                self.key_note = (name, f"Those keys already {other[0].lower() + other[1:]}. Pick different ones.")
            else:
                self.key_note = None
                self.stop_recording()
                self.pet.set_key(name, combo)
                self.changed_saved()
        self.draw()
        return "break"
