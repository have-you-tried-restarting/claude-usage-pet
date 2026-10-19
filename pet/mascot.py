# the Pet itself: puts the parts together, its settings, and starting it up.
import collections
import os
import queue
import random
import threading
import time
import tkinter as tk

from .art import KEY
from .cclog import ClaudeCodeLog
from .config import (FAKE_USAGE_ENV, MAX_SCALE, MIN_FETCH_GAP, MIN_SCALE, PROFILES, SETTINGS_FILE, SHINY_CHANCE,
    STATE_FILE)
from .bucket import BucketMixin
from .bungee import BungeeMixin
from .stunts import StuntsMixin
from .data import DataMixin
from .details import Details
from .dev import DevMixin
from .fun import FunMixin
from .gags import GagsMixin
from .hay import HayMixin
from .idle import IdleMixin
from .magic import MagicMixin
from .lines import TOUR_LINES
from .menu import PopupMenu
from .mouse import MouseMixin
from .movement import MovementMixin
from .render import RenderMixin
from .screens import ScreensMixin
from .settings_window import PERF_POINTS, SettingsWindow
from .storage import load_memory, load_settings, log_error, write_json
from .talk import TalkMixin
from .travel import TravelMixin
from .ui import Canvas, Fader
from .usage import CLOCK
from .winapi import hotkey_thread, make_dpi_aware, own_usage, set_startup, startup_path, summon_event, winmm


# ---- the pet ----

class Pet(ScreensMixin, MouseMixin, TalkMixin, DataMixin, MovementMixin, RenderMixin, FunMixin, MagicMixin,
          IdleMixin, TravelMixin, HayMixin, BucketMixin, BungeeMixin, StuntsMixin, GagsMixin, DevMixin):
    def __init__(self):
        make_dpi_aware()
        self.root = tk.Tk()
        self.root.overrideredirect(True)            # no title bar, no taskbar button
        self.root.attributes("-topmost", True)      # always on top
        self.root.configure(bg=KEY)
        self.root.attributes("-transparentcolor", KEY)
        self.dpi = self.root.winfo_fpixels("1i") / 96   # 1.0 at 100% display scaling, 1.5 at 150%
        self.canvas = Canvas(self.root, bg=KEY, highlightthickness=0, bd=0)
        self.canvas.pack()
        self.fonts, self.wraps = {}, {}

        st = load_settings()
        self.scale = st["scale"]
        self.energy = tk.StringVar(value=st["energy"])   # personality: how much it moves
        self.walk = tk.BooleanVar(value=st["energy"] != "statue")
        self.jump = tk.BooleanVar(value=st["energy"] != "statue")
        self.naps = tk.BooleanVar(value=st["naps"])
        self.anim = tk.BooleanVar(value=st["anim"])
        self.wizard = tk.BooleanVar(value=st["wizard"])
        self.warn = tk.BooleanVar(value=st["warn"])
        self.cc_app = tk.BooleanVar(value=st["cc_app"])
        self.warn_at = tk.IntVar(value=st["warn_at"])
        self.panic_at = tk.IntVar(value=st["panic_at"])
        self.poll = tk.IntVar(value=st["poll"])
        self.notify_on = tk.BooleanVar(value=st["notify"])
        self.sounds = tk.BooleanVar(value=st["sounds"])
        self.hotkeys = tk.BooleanVar(value=st["hotkeys"])
        self.platforms = tk.BooleanVar(value=st["platforms"])
        self.volume = tk.IntVar(value=st["volume"])
        self.hide_fs = tk.BooleanVar(value=st["hide_fs"])
        self.one_monitor = tk.BooleanVar(value=st["one_monitor"])
        self.bubble_mode = tk.StringVar(value=st["bubble"])
        self.bubble_style = tk.StringVar(value=st["bubble_style"])
        self.clock_fmt = tk.StringVar(value=st["clock"])   # 12h (3:05 PM) or 24h (15:05)
        self.dates = tk.StringVar(value=st["dates"])   # ddmm (Fri 16/10) or mmdd (Fri 10/16)
        self.clock_changed(save=False)
        self.chatter = tk.StringVar(value=st["chatter"])
        self.panel_tab = tk.StringVar(value=st["panel_tab"])
        self.cc_view = tk.StringVar(value=st["cc_view"])
        self.cc_range = tk.StringVar(value=st["cc_range"])
        self.plan_chart = tk.StringVar(value=st["plan_chart"])
        self.size_var = tk.DoubleVar(value=self.scale)
        self.pin_var = tk.BooleanVar(value=False)
        self.startup_var = tk.BooleanVar(value=startup_path().exists())
        self.tray_on = tk.BooleanVar(value=st["tray"])
        self.pace_warn = tk.BooleanVar(value=st["pace_warn"])     # heads-up when the pace runs out early
        self.seasonal = tk.BooleanVar(value=st["seasonal"])       # outfits on special days
        self.quiet_hours = tk.BooleanVar(value=st["quiet_hours"])
        self.quiet_from = tk.IntVar(value=st["quiet_from"])
        self.quiet_to = tk.IntVar(value=st["quiet_to"])
        self.dnd = tk.BooleanVar(value=st["dnd"])                 # quiet while windows' do not disturb is on
        self.rare = tk.BooleanVar(value=st["rare"])               # ufos, cats, a shiny colour
        self.apprentices = tk.BooleanVar(value=st["apprentices"]) # little helpers for parallel sessions
        self.bedtime = tk.BooleanVar(value=st["bedtime"])         # nightcap and candle at night
        self.bedtime_at = tk.IntVar(value=st["bedtime_at"])
        self.dev_setup(st["dev"])                                 # dev mode (pet/dev.py)

        # usage data, plus what it remembers from last time
        mem = load_memory()
        self.inbox = queue.Queue()
        self.data, self.error, self.updated = None, None, None
        self.busy = False
        self.next_at = 0.0          # unix time of the next check. 0 = check right away.
        self.blocked_until = mem["blocked_until"]   # the service said wait until then (kept over restarts)
        self.limited_at = mem["limited_at"]         # when the service last said "slow down" (checks slow down for a while)
        self.last_fetch = mem["last_fetch"]         # when we last asked the service (so a quick restart doesn't ask again)
        self.req_times, self.fetch_why, self.fetch_gap = [], "start", None
        self.why_next = "start"
        if not os.environ.get(FAKE_USAGE_ENV):
            self.next_at = max(self.next_at, self.last_fetch + MIN_FETCH_GAP)
        if self.blocked_until > time.time():
            self.next_at, self.error = self.blocked_until, self.rate_message()
        self.seen = mem["seen"]     # key -> (percent, when it last changed, resets_at)
        self.last_5h = mem["last_5h"]
        self.pokes = mem["pokes"]
        self.milestones = mem["milestones"]   # key -> [resets_at, levels already announced]
        self.last_usage = mem["last_usage"]   # when tokens last went up anywhere
        self.first_result = True
        self.history = mem["history"]   # [(time, 5-hour %, weekly %)] for the plan tab's chart
        self.greeted = mem["greeted"]    # the date it last said good morning
        self.last_ok = 0.0               # when the last good answer arrived (old numbers look faded)
        self.pace_warned = mem["pace_warned"]   # key -> resets_at of the window it already warned about
        self.recapped = mem["recapped"]         # claude code sessions it already wrapped up
        self.log, self.log_since = mem["log"], mem["log_since"]   # the diary: pokes, throws, jumps...
        self.hush_until = mem["hush_until"]     # quiet (menu) until then
        self.toured, self.season_said = mem["toured"], mem["season_said"]
        # lines to say one after another: the tour on the very first start, otherwise a welcome back
        self.script, self.next_line = ([] if self.toured else list(TOUR_LINES)), time.time() + 4
        self.welcome_due = self.toured
        self.shape_logged, self.win_quiet = False, False
        self.summon, self.tray = summon_event(), None   # starting it again calls it over; the tray icon
        self.creds_mtime = self.creds_changed_at()
        self.user_hidden = False         # hidden with ctrl + alt + P
        self.keys = queue.Queue()        # hotkey presses from the hotkey thread
        self.binds = st["keys"]          # the shortcuts: {"pet": [mods, key] or None, ...}
        self.hotkeys_on, self.keys_paused = self.hotkeys.get(), False   # (plain copies the thread can read)
        self.hotkey_tid, self.bind_ok = None, {}
        threading.Thread(target=hotkey_thread, args=(self.keys, self.wanted_keys), daemon=True).start()
        self.limited = 0                # "slow down" answers in a row
        self.failed = 0                 # other failed checks in a row (server errors, timeouts, refusals)

        # claude code's logs, read in the background
        self.cc = ClaudeCodeLog()
        self.cc.scan_ms = 0.0
        self.started, self.frames = time.time(), 0          # for the performance page
        self.checks_ok = self.checks_failed = 0
        self.perf = {"cpu": 0.0, "mem": 0.0, "fps": 0.0}
        self.perf_hist = collections.deque(maxlen=PERF_POINTS)   # (cpu, mem, fps) every 2 s, for the graphs
        self.settings_size = st["settings_size"]
        self.perf_prev = (time.perf_counter(), own_usage()[0], 0)
        self.root.after(2000, self.perf_tick)
        threading.Thread(target=self.cc.run, daemon=True).start()
        self.cc_growth_seen = 0.0
        self.working_until = 0.0
        self.was_working, self.work_started = False, 0.0
        self.next_work_line = self.next_idle_line = 0.0
        self.next_chat = time.time() + random.uniform(15, 45)
        self.speech, self.quiet_until = None, 0.0
        self.recent = collections.deque(maxlen=60)   # lines it said lately, so it doesn't repeat itself
        self.last_touch = time.time()             # last hover, poke or drag
        self.next_attention = self.next_full_line = self.next_late_line = 0.0
        self.error_seen, self.worried_t = time.time(), 0.0

        # screens. x is the pet's centre and y its feet, both in screen pixels.
        self.screens = self.get_screens()
        self.fs = [False] * len(self.screens)
        self.size, self.half, self.top_margin, self.bubble_top = (1, 1), 60, 0, 0
        sx, sy = st["x"], st["y"]
        if sx is not None and sy is not None and self.find_screen(sx, sy - 1) is not None:
            self.si = self.find_screen(sx, sy - 1)
            self.x, self.y = sx, self.screens[self.si].wb
        else:
            self.si = self.find_screen(0, 0) or 0
            sc = self.screens[self.si]
            self.x, self.y = sc.wr - 160 * self.dpi, sc.wb
        self.screens_at = time.time()

        # what it's doing
        self.vx, self.vy = 0.0, 0.0               # speed (vx is only for throws)
        self.angle, self.spin, self.hang = 0.0, 0.0, 0.0   # tilt while dragged or tumbling
        self.grab_local, self.grip, self.trail, self.drag_vx = (0, 0), (0, 0), [], 0.0
        self.chute, self.bounces = False, 0
        self.plat, self.plat_box, self.plats, self.plats_at = None, None, [], 0.0   # standing on a window
        self.ride_until, self.through = 0.0, False   # its window just moved / dropping through to the taskbar
        self.leap_plan, self.leaping = None, None   # jumping over to another window
        self.diving, self.hay_t = False, 0.0          # leap of faith, then sitting in the hay
        self.hay_show, self.hay_stage, self.straw_t, self.hay_flip = None, None, 0.0, 1   # (pet/hay.py)
        self.bucket = self.water = self.water_stage = None   # the water bucket jump and its water (pet/bucket.py)
        self.bungee = self.bungee_stage = None               # the bungee jump, its plank and cord (pet/bungee.py)
        self.stunt = self.stunt_stage = None                 # zipline, pole, web swing (pet/stunts.py)
        self.music, self.next_spell = False, 0.0      # dance music playing / when the wizard next goes zing
        self.muted = set(st["muted"])                 # sounds switched off in settings
        self.root.after(3000, self.warm_sounds)       # make the sound files early, in the background
        self.slapped = False                          # hit a window's side, on the way down
        self.near = []                                # windows near it while it's on the taskbar
        self.edge_turn = None
        self.goto_x = self.goto_why = None            # running somewhere (called over, fetch)
        self.dropping_in = self.ufo_fall = False
        self.ball = self.cat = self.ufo = None        # fetch, and rare visitors
        self.ball_sprite = self.cat_sprite = None
        self.fetch_at, self.cur_job, self.job_since = 0.0, None, 0.0   # (the wizard's job, and since when)
        self.act, self.act_t, self.act_info = None, 0.0, {}   # an idle activity (pet/idle.py)
        self.plane = self.plane_sprite = None         # a paper plane it threw
        self.trip, self.trip_stage = None, None      # on its way somewhere out of reach (pet/travel.py)
        self.walk_v = 0.0                             # walking speed right now (it speeds up and slows down)
        self.mouse = (-10 ** 6, -10 ** 6)             # where the pointer is (its eyes follow it)
        self.shiny, self.shiny_said = st["rare"] and random.random() < SHINY_CHANCE, False
        self.dizzy_t = self.stretch_t = self.dance_t = 0.0
        self.center_x, self.feet_win, self.body_at, self.pet_px = 0, 0, (0, 0), (72, 40)
        self.dir = random.choice((-1, 1))
        self.state, self.state_t = "idle", 2.0    # idle, walk, sleep, work or dance
        self.sleep_reason = None
        self.was_bedtime = None                   # was it in its pajamas last tick (None = just started)
        self.step, self.step_t = 0, 0.0
        self.blink_t, self.next_blink = 0.0, 3.0
        self.look_t, self.look_d = 0.0, 0         # glancing left or right while standing
        self.squash_t, self.pending_v = 0.0, 0.0  # crouch before a jump / squish after landing
        self.happy_t = self.wave_t = self.cast_t = 0.0
        self.celebrate = 0                        # hops left to celebrate a reset
        self.parts, self.part_t = [], 0.0         # floating hearts, z's and sparks
        self.clock = 0.0
        self.held = self.moved = self.pressed = False
        self.hidden = False                       # hidden because something is full screen
        self.hovering, self.hover_since, self.leave_at, self.hover_until = False, None, None, 0.0
        self.geo, self.last_frame, self.rects = None, None, {}
        self.anim_job, self.last_t = None, time.perf_counter()
        self.fine_timer, self.next_frame = False, time.perf_counter()
        self.saved_at = time.time()
        self.next_fs_check = self.next_slow_check = 0.0

        self.fader = Fader(self.root, 1.0, 1.0, self.place)
        self.details = Details(self)
        self.settings = SettingsWindow(self)
        self.popup = PopupMenu(self)
        c = self.canvas
        c.bind("<Button-1>", self.press)
        c.bind("<B1-Motion>", self.motion)
        c.bind("<ButtonRelease-1>", self.release)
        c.bind("<Button-3>", self.show_menu)
        self.root.bind_all("<Control-MouseWheel>", self.wheel)

        self.root.report_callback_exception = lambda *exc: log_error(f"inside the pet (doing: {getattr(self, 'state', '?')})", exc)
        self.redraw()
        self.data_tick()
        self.ui_tick()
        if self.anim.get():
            self.start_anim()

    def show_menu(self, e):
        if self.popup.visible:   # right-clicking again closes it
            self.popup.hide()
            return
        if not self.details.pinned:
            self.details.hide()   # the hover panel would otherwise pop up over the menu and catch its clicks
        # open beside the mascot's body, not on top of it, so the mascot stays clickable
        pw, ph = self.pet_px
        bx, by = (self.geo[2] + self.body_at[0], self.geo[3] + self.body_at[1]) if self.geo else (e.x_root, e.y_root)
        self.popup.show(e.x_root, e.y_root, avoid=(bx, by, bx + pw, by + ph))

    # settings
    def s(self):
        # your size setting times the display scaling of the monitor it's on
        return self.scale * self.screens[self.si].dpi

    def save(self):
        st = {k: (v.get() if isinstance(v, tk.Variable) else v) for k, v in (
            ("scale", self.scale), ("energy", self.energy), ("walk", self.walk), ("jump", self.jump), ("naps", self.naps),
            ("anim", self.anim), ("bubble", self.bubble_mode), ("bubble_style", self.bubble_style), ("clock", self.clock_fmt), ("dates", self.dates),
            ("chatter", self.chatter), ("wizard", self.wizard), ("warn", self.warn), ("cc_app", self.cc_app), ("warn_at", self.warn_at), ("panic_at", self.panic_at), ("poll", self.poll),
            ("notify", self.notify_on), ("sounds", self.sounds), ("hotkeys", self.hotkeys),
            ("platforms", self.platforms), ("volume", self.volume), ("muted", sorted(self.muted)), ("keys", self.binds), ("settings_size", self.settings_size), ("hide_fs", self.hide_fs),
            ("one_monitor", self.one_monitor), ("panel_tab", self.panel_tab), ("cc_view", self.cc_view),
            ("cc_range", self.cc_range), ("plan_chart", self.plan_chart), ("x", round(self.x)), ("y", round(self.y)),
            ("tray", self.tray_on), ("pace_warn", self.pace_warn), ("seasonal", self.seasonal),
            ("quiet_hours", self.quiet_hours), ("quiet_from", self.quiet_from), ("quiet_to", self.quiet_to),
            ("dnd", self.dnd), ("rare", self.rare), ("apprentices", self.apprentices),
            ("bedtime", self.bedtime), ("bedtime_at", self.bedtime_at), ("dev", self.dev_on))}
        write_json(SETTINGS_FILE, st)
        write_json(STATE_FILE, {"seen": self.seen, "last_5h": self.last_5h, "pokes": self.pokes,
                                "history": self.history, "greeted": self.greeted,
                                "milestones": self.milestones, "last_usage": self.last_usage,
                                "pace_warned": self.pace_warned, "recapped": self.recapped,
                                "log": {k: round(v, 1) if isinstance(v, float) else v for k, v in self.log.items()},
                                "log_since": self.log_since, "hush_until": self.hush_until,
                                "toured": self.toured, "season_said": self.season_said,
                                "blocked_until": self.blocked_until, "last_fetch": self.last_fetch,
                                "limited_at": self.limited_at})
        self.saved_at = time.time()

    def changed(self):
        self.redraw()
        self.save()

    def set_scale(self, v):
        self.scale = round(min(MAX_SCALE, max(MIN_SCALE, v)), 3)
        self.size_var.set(self.scale)
        self.redraw()
        if self.details.visible:
            self.details.draw()
        self.save()

    def wheel(self, e):
        self.set_scale(self.scale * (1.1 if e.delta > 0 else 1 / 1.1))

    def anim_changed(self):
        if self.anim.get():
            self.start_anim()
        else:
            if self.anim_job:
                self.root.after_cancel(self.anim_job)
                self.anim_job = None
            self.wake(hop=False)
            self.end_trip()
            self.plat = None
            self.y, self.vy = self.screens[self.si].wb, 0.0   # land and stand still
            self.state, self.squash_t, self.pending_v, self.parts = "idle", 0.0, 0.0, []
            self.happy_t = self.wave_t = self.look_t = 0.0
            self.celebrate = 0
        self.changed()

    def cc_stats(self):
        # the claude code numbers, counted like the claude app or for real
        st = self.cc.stats
        return st and st["app" if self.cc_app.get() else "real"]

    def cc_changed(self):
        if self.details.visible:
            self.details.draw()
        self.save()

    def poll_changed(self):
        self.next_at = max(self.blocked_until, min(self.next_at, time.time() + self.expected_gap()))
        self.changed()

    def clock_changed(self, save=True):
        CLOCK["24h"], CLOCK["mmdd"] = self.clock_fmt.get() == "24h", self.dates.get() == "mmdd"
        if save:
            if self.details.visible:
                self.details.draw()
            self.save()

    def prof(self):
        return PROFILES[self.energy.get()]

    def energy_changed(self):
        moving = self.energy.get() != "statue"
        self.walk.set(moving)
        self.jump.set(moving)
        if not moving and self.state == "walk":
            self.state, self.state_t = "idle", 2.0
        self.changed()

    def naps_changed(self):
        if not self.naps.get():
            self.wake()
        self.changed()

    def chatter_changed(self):
        if self.chatter.get() == "off":
            self.speech = None
        self.changed()

    def hide_fs_changed(self):
        self.check_fullscreen()
        self.changed()

    def pin_changed(self):
        if self.pin_var.get():
            self.details.show(pinned=True)
        else:
            self.details.hide()

    def startup_changed(self):
        set_startup(self.startup_var.get())
        self.startup_var.set(startup_path().exists())   # show what really happened

    def quit(self):
        if self.fine_timer and winmm:
            winmm.timeEndPeriod(1)
        if self.tray is not None:
            self.tray.hide()   # (or windows leaves a ghost icon by the clock until you hover it)
        self.save()
        self.root.destroy()
