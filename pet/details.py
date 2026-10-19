# the details panel that shows when you hover the mascot (plan and claude code tabs).
import datetime
import math
import time
import tkinter as tk
import tkinter.font as tkfont

from .art import IDLE_C, PARK, RED
from .cclog import compare_line, fmt_minutes, fmt_money, fmt_tokens, hour_label, pretty_model
from .config import CONTEXT_TIP_PCT, IDLE_AFTER_MIN, IDLE_POLL_SECONDS, SESSION_DONE_MIN
from .ui import Canvas, Fader, Tooltip, move_window, round_corners, round_rect, to_front
from .usage import (bar_color, fmt_day, fmt_time, fmt_when, forecast, pace_info, parse_rows, parse_time,
    period_seconds, reset_text)


# ---- details panel (hover the mascot) ----

PANEL_W = 340
HEAT = ["#3a3936", "#173c6e", "#1f57a6", "#2b74e0", "#5aa2ff"]   # empty day, then busier and busier
VIEWS = (("overview", "Overview"), ("models", "Models"), ("projects", "Projects"), ("sessions", "Sessions"))
RANGES = (("7d", "7 days"), ("30d", "30 days"), ("all", "All time"))

class Details:
    # styled like the claude desktop app (and the settings window): warm greys, segmented controls,
    # sections as small headings over rounded cards, claude's orange for accents
    BG, CARD, LINE, WELL, SEL = "#262624", "#30302e", "#3d3d3a", "#1f1e1d", "#46453f"
    FG, DIM, FAINT, ON = "#faf9f5", "#a6a39a", "#6b6a65", "#d97757"
    FASTC, SLOWC = "#e8a33d", "#6aa9ff"
    FIXC = "#6aa9ff"   # what to do about an error

    def __init__(self, pet):
        self.pet = pet
        self.win = tk.Toplevel(pet.root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", 0.0)
        self.win.configure(bg=self.BG)
        self.win.geometry(f"10x10+{PARK}+{PARK}")   # starts parked off screen
        self.canvas = Canvas(self.win, bg=self.BG, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<ButtonRelease-1>", self.click)
        self.canvas.bind("<Button-3>", pet.show_menu)
        self.canvas.bind("<Motion>", self.hover)
        self.canvas.bind("<Leave>", lambda e: self.hide_tip())
        self.tips = []   # (x1, y1, x2, y2, text) areas that explain themselves
        self.tooltip = Tooltip(self.win, self.CARD, self.FG, self.DIM, self.font)
        self.visible = self.pinned = self.rounded = False
        self.hits, self.rect, self.px_size, self.fonts = [], None, (10, 10), {}
        self.anchor_x = self.anchor_bottom = 0
        self.avoid = (0, 0, 0, 0)
        self.s = 1.0
        self.curve_key, self.curve = None, []   # cached estimate for the plan chart
        self.fader = Fader(self.win, 0.0, 1.0, self.place)

    def show(self, pinned=False):
        p = self.pet
        self.pinned = self.pinned or pinned
        p.pin_var.set(self.pinned)
        if self.visible:
            return
        self.visible = True
        self.anchor_x = p.x   # opens just above the bubble if there's room
        self.anchor_bottom = (p.geo[3] if p.geo else p.screens[p.si].wb) + p.top_margin - round(6 * p.dpi)
        # the space the mascot and its bubble take up, which the panel must not cover
        self.avoid = (round(p.x - p.half), self.anchor_bottom, round(p.x + p.half), round(p.y))
        self.draw()
        if not self.rounded:
            round_corners(self.win)
            self.rounded = True
        self.to_front()
        self.fader.to(1.0, instant=not p.anim.get())

    def to_front(self):
        # in front of every other always-on-top window. runs on show and every second while it's open
        # (data_tick), with its tooltip and the right-click menu kept in front of it.
        to_front(self.win)
        if self.tooltip.win is not None and self.tooltip.text is not None:
            to_front(self.tooltip.win)
        if self.pet.popup.visible:
            to_front(self.pet.popup.win)

    def hide(self):
        self.hide_tip()
        if not self.visible:
            return
        self.visible = self.pinned = False
        self.pet.pin_var.set(False)
        self.fader.to(0.0, instant=not self.pet.anim.get())

    def place(self):
        p = self.pet
        if not self.visible and self.fader.alpha <= 0.001:
            move_window(self.win, PARK, PARK)
            self.rect = None
            return
        pw, ph = self.px_size
        sc = p.screens[p.si]
        gap = round(8 * p.dpi)
        left, top, right, feet = self.avoid
        x = min(max(sc.wl + 4, round(self.anchor_x - pw / 2)), sc.wr - pw - 4)
        if self.anchor_bottom - ph >= sc.wt + 4:
            y = self.anchor_bottom - ph            # above the bubble (the usual place)
        elif feet + gap + ph <= sc.wb - 4:
            y = feet + gap                         # high up (on a window): below the mascot instead
        else:                                      # no room above or below: beside it
            x = right + gap if right + gap + pw <= sc.wr - 4 else max(sc.wl + 4, left - gap - pw)
            y = min(max(sc.wt + 4, feet - ph), sc.wb - ph - 4)
        self.rect = (x, y, x + pw, y + ph)
        y += round((1 - self.fader.alpha) * 10 * p.dpi)   # slides up a little as it fades in
        move_window(self.win, x, y, pw, ph)

    def hover(self, e):
        for x1, y1, x2, y2, text in self.tips:
            if x1 <= e.x <= x2 and y1 <= e.y <= y2:
                return self.show_tip(text, e)
        self.hide_tip()

    def show_tip(self, text, e):
        self.tooltip.show(text, e.x_root, e.y_root, self.s)

    def hide_tip(self):
        self.tooltip.hide()

    def click(self, e):
        p = self.pet
        for name, x1, y1, x2, y2 in self.hits:
            if x1 <= e.x <= x2 and y1 <= e.y <= y2:
                if name == "close":
                    self.hide()
                    return
                kind, val = name.split(":")
                {"tab": p.panel_tab, "view": p.cc_view, "range": p.cc_range, "chart": p.plan_chart}[kind].set(val)
                self.draw()
                p.save()
                return

    # ---- drawing helpers. positions are in base units (PANEL_W wide) times self.s ----
    def font(self, size, bold=False):
        px = max(8, round(size * 4 / 3 * self.s))
        if (px, bold) not in self.fonts:
            self.fonts[(px, bold)] = tkfont.Font(root=self.win, family="Segoe UI", size=-px,
                                                 weight="bold" if bold else "normal")
        return self.fonts[(px, bold)]

    def text(self, x, y, text, fill, size, bold=False, anchor="nw", width=None):
        kw = {"width": width * self.s} if width else {}
        item = self.canvas.create_text(x * self.s, y * self.s, anchor=anchor, fill=fill, font=self.font(size, bold),
                                       text=text, **kw)
        return self.canvas.bbox(item)[3] / self.s   # where the text ends, for wrapped lines

    def rect_(self, x1, y1, x2, y2, fill):
        s = self.s
        self.canvas.create_rectangle(x1 * s, y1 * s, x2 * s, y2 * s, fill=fill, width=0)

    def box(self, x1, y1, x2, y2, r, fill, bg=None):
        s = self.s
        round_rect(self.canvas, x1 * s, y1 * s, x2 * s, y2 * s, r * s, fill, bg or self.BG, True)

    def line(self, x1, y1, x2, y2, fill, width=1):
        s = self.s
        self.canvas.create_line(x1 * s, y1 * s, x2 * s, y2 * s, fill=fill, width=max(1, round(width * s)))

    def bar(self, x1, y, x2, frac, color, bg=None):
        # a rounded progress bar on a darker track
        self.box(x1, y, x2, y + 6, 3, self.WELL, bg or self.CARD)
        if frac > 0:
            self.box(x1, y, max(x1 + 6, x1 + (x2 - x1) * min(1.0, frac)), y + 6, 3, color, self.WELL)

    def segmented(self, x0, y, x1, options, current, hit, size=8, h=26, equal=False):
        # like the claude app: options share a dark well, the chosen one sits on a lighter tab
        f = self.font(size, True)
        widths = [f.measure(label) / self.s + 18 for _, label in options]
        if x1 is None:   # just as wide as it needs to be (x0 is then its right edge)
            x1, x0 = x0, x0 - sum(widths) - 6
        elif equal:      # spread across the space given, every option the same width
            widths = [(x1 - x0 - 6) / len(options)] * len(options)
        else:            # spread across the space given
            extra = (x1 - x0 - 6 - sum(widths)) / len(options)
            widths = [w + extra for w in widths]
        self.box(x0, y, x1, y + h, 8, self.WELL)
        x = x0 + 3
        for (value, label), w in zip(options, widths):
            on = current == value
            if on:
                self.box(x, y + 3, x + w, y + h - 3, 6, self.SEL, self.WELL)
            self.text(x + w / 2, y + h / 2, label, self.FG if on else self.DIM, size, True, "center")
            self.hits.append((f"{hit}:{value}", x * self.s, y * self.s, (x + w) * self.s, (y + h) * self.s))
            x += w
        return x0

    def heading(self, y, label, right=None, right_color=None):
        # a small section heading over a card, like the settings window
        self.text(14, y, label, self.DIM, 8, True)
        if right:
            self.text(PANEL_W - 14, y, right, right_color or self.FAINT, 7.5, anchor="ne")
        return y + 20

    def card(self, y0, y1):
        # drawn after what's in it (its height is only known then), so it's sent to the back
        s = self.s
        round_rect(self.canvas, 12 * s, y0 * s, (PANEL_W - 12) * s, y1 * s, 10 * s, self.CARD, self.BG, True, "card")
        self.canvas.tag_lower("card")

    # ---- the whole panel ----
    def draw(self):
        p = self.pet
        self.s = s = p.dpi * min(1.6, max(1.0, p.scale))
        # every tab and view gets the same height, so nothing jumps when you switch
        tallest = 0
        for tab, view in (("plan", None), ("cc", "overview"), ("cc", "models"), ("cc", "projects"),
                          ("cc", "sessions")):
            tallest = max(tallest, self.draw_tab(tab, view))
        self.draw_tab(p.panel_tab.get(), p.cc_view.get())
        H = tallest + 10
        self.px_size = (round(PANEL_W * s), round(H * s))
        self.canvas.configure(width=self.px_size[0], height=self.px_size[1])
        self.place()

    def draw_tab(self, tab, view):
        # draws one tab from scratch and returns how tall it came out
        s, W = self.s, PANEL_W
        self.canvas.delete("all")
        self.hits, self.tips = [], []
        self.segmented(12, 12, W - 44, (("plan", "Plan"), ("cc", "Claude Code")), tab, "tab", 8.5, 30, equal=True)
        self.text(W - 22, 27, "×", self.DIM, 13, False, "center")      # close button
        self.hits.append(("close", (W - 38) * s, 10 * s, (W - 6) * s, 44 * s))
        return self.draw_plan(54) if tab == "plan" else self.draw_cc(54, view)

    # ---- plan tab ----
    def draw_plan(self, y):
        p = self.pet
        W = PANEL_W
        rows = parse_rows(p.data) if p.data else []
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        now = time.time()
        left = max(0, math.ceil(p.next_at - now))
        wait = "updating…" if p.busy else f"next check in {left // 60}m {left % 60:02d}s" if left >= 60             else f"next check in {left}s"
        right = (f"updated {fmt_time(p.updated)} · " if p.updated else "") + wait
        idle = not p.busy and p.idle(now)
        y = self.heading(y, "Your plan", ("idle · " + right) if idle else right, IDLE_C if idle else None)
        if idle:   # hovering the line says why the checks are slower
            tw = self.font(7.5).measure("idle · " + right) / self.s
            self.tips.append(((W - 14 - tw) * self.s, (y - 20) * self.s, (W - 14) * self.s, (y - 6) * self.s,
                              f"Idle: Claude hasn't been used for {IDLE_AFTER_MIN} min, so it checks every "
                              f"{IDLE_POLL_SECONDS // 60} min. Back to normal as soon as you use Claude."))
        if p.quiet():   # no talking or sounds right now
            until = (f" until {fmt_time(datetime.datetime.fromtimestamp(p.hush_until))}"
                     if time.time() < p.hush_until else "")
            y = self.text(14, y - 4, f"Quiet mode{until}: no talking or sounds.", self.SLOWC, 7.5) + 6
        top = y
        y += 12
        for i, r in enumerate(rows):
            if i:
                self.line(26, y - 6, W - 26, y - 6, self.LINE)
            seen = p.seen.get(r["key"])
            unchanged = now - seen[1] if seen else 0
            el, msg, kind = pace_info(r["key"], r["pct"], r["resets"], now_dt, unchanged)
            self.text(26, y, r["label"] + " limit", self.FG, 9, True)
            self.text(W - 26, y, f"{r['pct']:.0f}%", self.FG, 9, True, "ne")
            self.bar(26, y + 22, W - 26, r["pct"] / 100, bar_color(r["pct"]))
            if el is not None:   # the pace tick: where the clock is in this window
                tx = 26 + (W - 52) * el / 100
                self.line(tx, y + 18, tx, y + 32, self.FG, 2)
            when = parse_time(r["resets"])
            at = f" · {fmt_when(when.astimezone(), r['key'])}" if when else ""
            y = self.text(26, y + 36, reset_text(r["resets"], now_dt).capitalize() + at, self.DIM, 7.5) + 2
            if msg:
                y = self.text(26, y, msg[0].upper() + msg[1:], self.FASTC if kind == "fast" else self.SLOWC, 7.5,
                              True, width=W - 52) + 2
            y += 14
        if p.error:   # the problem in red, then what to do about it (or that it sorts itself out) in blue
            head, _, steps = p.error.partition(chr(10) * 2)
            y = self.text(26, y, head[0].upper() + head[1:], RED, 8, True, width=W - 52) + 6
            if steps:
                y = self.text(26, y, steps, self.FIXC, 7.5, width=W - 52) + 8
        elif not rows:
            y = self.text(26, y, "Loading…", self.DIM, 8) + 12
        self.card(top, y)
        y += 14
        if rows:
            y = self.draw_chart(y, rows, now_dt)
        y = self.draw_context(y)
        st = p.cc_stats()
        if st:
            y = self.text(14, y, f"Claude Code today: {fmt_tokens(st['today'])} tokens · about "
                                 f"{fmt_money(st['today_cost'])} at API prices", self.FAINT, 7.5, width=W - 28) + 4
        return y

    def draw_context(self, y):
        # how full the latest claude code chat's context is
        info = self.pet.cc.context_info()
        if info is None:
            return y
        y = self.heading(y, "Context window", f"latest Claude Code chat · {fmt_minutes(time.time() - info['when'].timestamp())} ago")
        top = y
        y += 12
        name = self.pet.cc.titles.get(info["session"], "Latest chat")
        self.text(26, y, name if len(name) <= 34 else name[:33] + "…", self.FG, 9, True)
        self.text(PANEL_W - 26, y, f"{info['pct']:.0f}% full", self.FG, 9, True, "ne")
        self.bar(26, y + 22, PANEL_W - 26, info["pct"] / 100, bar_color(info["pct"]))
        y = self.text(26, y + 36, f"{fmt_tokens(info['tokens'])} of {fmt_tokens(info['window'])} tokens: how much of the "
                                  "chat Claude is holding in mind", self.DIM, 7.5, width=PANEL_W - 52) + 2
        if info["pct"] >= CONTEXT_TIP_PCT:   # getting full: say what to do about it
            y = self.text(26, y + 4, "Getting full. Type /compact to have Claude sum up the chat so far and carry on with "
                                 "room to spare, or /clear to start a fresh chat (Claude forgets this one). Claude Code "
                                 "compacts by itself when it's nearly full.", self.FIXC, 7.5, width=PANEL_W - 52) + 2
        y += 12
        self.card(top, y)
        return y + 14

    def draw_chart(self, y, rows, now_dt):
        # usage so far in the current window, against the pace line, plus a forecast
        p, s, W = self.pet, self.s, PANEL_W
        which = p.plan_chart.get()
        key = "five_hour" if which == "5h" else "seven_day"
        r = next((r for r in rows if r["key"] == key), None)
        self.text(14, y + 11, "This window", self.DIM, 8, True, "w")
        self.segmented(W - 12, y, None, (("5h", "5-hour"), ("7d", "Week")), which, "chart", 7.5, 22)
        y += 30
        top = y
        reset = parse_time(r["resets"]) if r else None
        if not r or reset is None:
            y = self.text(26, y + 14, "No data for this limit yet.", self.DIM, 8) + 14
            self.card(top, y)
            return y + 12
        period = period_seconds(key)
        start = reset.timestamp() - period
        now = time.time()
        pts = [(h[0], h[1] if key == "five_hour" else h[2]) for h in p.history if h[0] >= start]
        pts = [(tt, v) for tt, v in pts if v is not None]
        # before the pet's first check in this window there's no real data. estimate it from when
        # claude code used tokens, scaled so it meets the first real number. drawn dotted.
        first_t, first_v = pts[0] if pts else (now, r["pct"])
        est = []
        if first_t - start > 300 and first_v > 0:
            ck = (round(start), round(first_t), len(p.cc.answers))
            if self.curve_key != ck:
                self.curve_key, self.curve = ck, p.cc.usage_curve(start, first_t)
            if self.curve and self.curve[-1][1] > 0:
                k = first_v / self.curve[-1][1]
                est = [(start, 0.0)] + [(tt, v * k) for tt, v in self.curve] + [(first_t, first_v)]
            else:
                est = [(start, 0.0), (first_t, first_v)]
        pts = pts + [(now, r["pct"])]
        # the chart, in a dark well inside the card
        x0, x1, y0, y1 = 24, W - 24, y + 12, y + 88
        self.box(x0, y0, x1, y1, 7, self.WELL, self.CARD)
        ix0, ix1, iy0, iy1 = x0 + 8, x1 - 8, y0 + 8, y1 - 8
        fx = lambda tt: ix0 + (ix1 - ix0) * min(1.0, max(0.0, (tt - start) / period))
        fy = lambda v: iy1 - (iy1 - iy0) * min(100.0, max(0.0, v)) / 100
        for v in (50, 100):   # faint guide lines at 50% and 100%
            self.rect_(ix0, fy(v), ix1, fy(v) + 0.6, self.LINE)
        self.text(ix0 + 2, fy(100) + 1, "100%", self.FAINT, 6.5)
        # the pace line: where you'd be if you used it evenly until the reset
        self.canvas.create_line(fx(start) * s, fy(0) * s, fx(reset.timestamp()) * s, fy(100) * s,
                                fill=self.FAINT, width=max(1, round(s)), dash=(3, 3))
        color = bar_color(r["pct"])
        if est:
            line = []
            for tt, v in est:
                line += [fx(tt) * s, fy(v) * s]
            self.canvas.create_line(*line, fill=color, width=max(2, round(2 * s)), dash=(2, 3))
        if len(pts) >= 2:
            line = []
            for tt, v in pts:
                line += [fx(tt) * s, fy(v) * s]
            self.canvas.create_line(*line, fill=color, width=max(2, round(2 * s)))
        nx, ny = fx(now) * s, fy(r["pct"]) * s
        d = max(3, round(3 * s))
        self.canvas.create_oval(nx - d, ny - d, nx + d, ny + d, fill=color, outline="")
        if len(pts) < 2 and not est:
            self.text((ix0 + ix1) / 2, iy0 + 16, "the line fills in as I check your usage", self.DIM, 7.5,
                      anchor="n")
        st_dt = datetime.datetime.fromtimestamp(start)
        self.text(x0, y1 + 4, fmt_time(st_dt) if key == "five_hour" else fmt_day(st_dt), self.FAINT, 7)
        self.text(x1, y1 + 4, f"resets {fmt_when(reset.astimezone(), key)}", self.FAINT, 7, anchor="ne")
        if est:
            self.text((x0 + x1) / 2, y1 + 4, "dotted = estimate", self.FAINT, 7, anchor="n")
        y = y1 + 22
        # the forecast
        fc = forecast(key, r["pct"], r["resets"], now_dt)
        if fc is None:
            msg, col = "Too early in this window for a forecast.", self.DIM
        else:
            proj, out = fc
            if out is not None:
                left = reset.timestamp() - out
                gap = f"{left / 3600:.0f}h" if left >= 3600 else f"{left / 60:.0f}m"
                msg, col = (f"At this pace you'll run out around {fmt_when(datetime.datetime.fromtimestamp(out), key)}, "
                            f"about {gap} before the reset."), self.FASTC
            elif r["pct"] >= 100:
                msg, col = "All used up. It comes back at the reset.", RED
            else:
                msg, col = f"At this pace you'll use about {proj:.0f}% by the reset.", "#4caf7d"
        y = self.text(26, y, msg, col, 8, True, width=W - 52) + 12
        self.card(top, y)
        return y + 12

    # ---- claude code tab ----
    def draw_cc(self, y, view):
        p = self.pet
        W = PANEL_W
        self.segmented(12, y, W - 12, VIEWS, view, "view", 8, 28)
        y += 40
        st = p.cc_stats()
        if view == "sessions":
            return self.draw_sessions(y, st)
        rng = p.cc_range.get()
        self.text(14, y + 11, "Showing", self.DIM, 8, True, "w")
        self.segmented(W - 12, y, None, RANGES, rng, "range", 7.5, 22)
        y += 32
        if st is None:
            return self.text(14, y, "Reading Claude Code's logs…", self.DIM, 8) + 20
        r = st["ranges"][rng]
        if not r["messages"]:
            return self.text(14, y, "No Claude Code activity on this computer in this period.", self.DIM, 8,
                             width=W - 28) + 34
        if view == "overview":
            y = self.draw_overview(y, st, r)
        elif view == "projects":
            y = self.draw_list(y, [(name if len(name) <= 30 else name[:29] + "…", tok,
                                    f"{n} session{'s' if n != 1 else ''}") for name, tok, n in r["projects"][:5]],
                               r["tokens"], "#6aa9ff")
            rest = r["projects"][5:]
            if rest:   # the smaller ones, one line each in a card of their own
                top = y
                y += 10
                for name, tok, n in rest[:10]:
                    name = name if len(name) <= 30 else name[:29] + "…"
                    self.text(26, y, name, self.DIM, 8)
                    y = self.text(W - 26, y, f"{fmt_tokens(tok)} · {100 * tok / (r['tokens'] or 1):.0f}%",
                                  self.DIM, 8, False, "ne") + 4
                if len(rest) > 10:
                    y = self.text(26, y, f"and {len(rest) - 10} more", self.FAINT, 7.5) + 4
                self.card(top, y + 6)
                y += 18
        else:
            y = self.draw_list(y, [(pretty_model(m), t, None) for m, t in r["models"][:4]], r["tokens"], self.ON)
            i_, o_, w_, r_ = r["parts"]
            y = self.heading(y, "Token types")
            top = y
            for i, (label, n) in enumerate((("Input", i_), ("Output", o_), ("Cache write", w_), ("Cache read", r_))):
                cx = 26 + (i % 2) * (W - 52) / 2
                cy = y + 12 + (i // 2) * 22
                self.text(cx, cy, label, self.DIM, 8)
                self.text(cx + (W - 52) / 2 - 12, cy, fmt_tokens(n), self.FG, 8, True, "ne")
            y += 12 + 44 + 4
            self.card(top, y)
            y = self.text(14, y + 10, self.cost_line(r), self.FAINT, 7.5, width=W - 28) + 6
        how = ("Counted like the Claude app (every logged copy), from this computer's logs." if p.cc_app.get()
               else "Real count (each answer once), from this computer's logs.")
        return self.text(14, y, how, self.FAINT, 7, width=W - 28) + 4

    def draw_overview(self, y, st, r):
        W, s = PANEL_W, self.s
        fav = pretty_model(r["models"][0][0]) if r["models"] else "–"
        tiles = [("Sessions", f"{r['sessions']:,}"), ("Messages", f"{r['messages']:,}"),
                 ("Total tokens", fmt_tokens(r["tokens"])), ("Active days", f"{r['days']:,}"),
                 ("Peak hour", "–" if r["peak"] is None else hour_label(r["peak"])), ("Favourite model", fav)]
        top = y
        cw = (W - 24) / 3
        for i, (label, val) in enumerate(tiles):   # one card, split into six tiles by thin lines
            cx, cy = 12 + (i % 3) * cw, y + (i // 3) * 50
            self.text(cx + 14, cy + 10, label, self.DIM, 7.5)
            self.text(cx + 14, cy + 25, val, self.FG, 10, True)
        y += 100
        self.card(top, y)
        for i in (1, 2):
            self.line(12 + i * cw, top + 10, 12 + i * cw, y - 10, self.LINE)
        self.line(24, top + 50, W - 24, top + 50, self.LINE)
        y = self.heading(y + 12, "Activity", "last 26 weeks")
        top = y
        # one square per day, sunday at the top
        heat, today = st["heat"], datetime.date.today()
        start = today - datetime.timedelta(days=(today.weekday() + 1) % 7 + 7 * 25)
        busiest = max([v for d, v in heat.items() if d >= start] or [0])
        pitch = int((W - 52) * s // 26)            # whole pixels, so every square is the same size
        cell = pitch - max(2, round(2 * s))
        gx, gy = round(26 * s), round((y + 12) * s)
        self.card(top, y + 12 + 7 * pitch / s + 12)
        for col in range(26):
            for row in range(7):
                d = start + datetime.timedelta(days=col * 7 + row)
                if d > today:
                    continue
                v = heat.get(d, 0)
                lvl = 1 + min(3, int(4 * v / busiest)) if v and busiest else 0
                x0, y0 = gx + col * pitch, gy + row * pitch
                self.canvas.create_rectangle(x0, y0, x0 + cell, y0 + cell, fill=HEAT[lvl], width=0)
        y += 12 + 7 * pitch / s + 22
        y = self.text(14, y, compare_line(r["tokens"]), self.DIM, 7.5, width=W - 28) + 3
        return self.text(14, y, self.cost_line(r), self.DIM, 7.5, width=W - 28) + 8

    def draw_list(self, y, items, total, color):
        # rows of name, tokens and share, with a bar each, in one card
        W = PANEL_W
        top = y
        y += 14
        total = total or 1
        for i, (name, tok, sub) in enumerate(items):
            if i:
                self.line(26, y - 7, W - 26, y - 7, self.LINE)
            self.text(26, y, name, self.FG, 8.5, True)
            self.text(W - 26, y, f"{fmt_tokens(tok)} · {100 * tok / total:.0f}%", self.FG, 8.5, True, "ne")
            self.bar(26, y + 20, W - 26, tok / total, color)
            y += 32
            if sub:
                y = self.text(26, y - 2, sub, self.DIM, 7) + 2
            y += 8
        self.card(top, y)
        return y + 12

    def draw_sessions(self, y, st):
        # the latest claude code sessions, newest first: a recap of each
        p, W = self.pet, PANEL_W
        y = self.heading(y + 4, "Latest sessions", "on this computer")
        if st is None:
            return self.text(14, y, "Reading Claude Code's logs…", self.DIM, 8) + 20
        recent = st.get("recent", [])[:5]
        if not recent:
            return self.text(14, y, "No sessions yet.", self.DIM, 8) + 24
        now = time.time()
        top = y
        y += 14
        for i, ses in enumerate(recent):
            if i:
                self.line(26, y - 7, W - 26, y - 7, self.LINE)
            start = ses["start"]
            label = ses["project"] if len(ses["project"]) <= 26 else ses["project"][:25] + "…"
            self.text(26, y, label, self.FG, 8.5, True)
            self.text(W - 26, y, f"{fmt_tokens(ses['tokens'])} tokens", self.FG, 8.5, True, "ne")
            busy = now - max(ses["end"].timestamp(), p.cc.active.get(ses["id"], 0.0)) < SESSION_DONE_MIN * 60
            mins = fmt_minutes((ses["end"] - start).total_seconds())
            end = self.text(26, y + 19, f"{fmt_day(start)} {fmt_time(start)} · {mins} · {ses['messages']} messages",
                            self.DIM, 7.5)
            if busy:   # still going: a small orange pill
                f = self.font(7, True)
                w = f.measure("Active") / self.s + 12
                self.box(W - 26 - w, y + 19, W - 26, y + 33, 7, "#4a3128", self.CARD)
                self.text(W - 26 - w / 2, y + 26, "Active", self.ON, 7, True, "center")
            model = pretty_model(ses["model"]) + " · " if ses["model"] else ""
            y = self.text(26, end + 1, f"{model}about {fmt_money(ses['cost'])} at API prices", self.FAINT, 7.5) + 14
        self.card(top, y - 4)
        how = ("Tokens counted like the Claude app." if p.cc_app.get() else "Tokens counted once per answer.")
        return self.text(14, y + 6, how + f" A session counts as finished after {SESSION_DONE_MIN} minutes with "
                         "nothing new.", self.FAINT, 7, width=W - 28) + 4

    def cost_line(self, r):
        # what these tokens would cost on the pay-as-you-go api (always counted once)
        extra = " (some models have no price here)" if r["unpriced"] else ""
        return f"About {fmt_money(r['cost'])} at API prices{extra}. Your plan covers this; it's for comparison."
