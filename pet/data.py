# part of the Pet: fetching usage, milestones, keyboard shortcuts and the regular ticks.
import datetime
import os
import queue
import random
import threading
import time

from . import usage
from .art import DIM, IDLE_C, RED
from .config import (CONTEXT_FRESH_MIN, DEFAULT_KEYS, FAKE_USAGE_ENV, IDLE_AFTER_MIN, IDLE_POLL_SECONDS, ERROR_RETRY_MAX, MIN_FETCH_GAP,
    NICE, PACE_WARN, RATE_LIMITED_MAX, RATE_LIMITED_SECONDS, REFUSED_RETRY_SECONDS, SHORT, SLOW_AFTER_LIMIT, STALE_MIN)
from .lines import MILESTONES, PACE_LINES, RESET_LINES
from .storage import log_error, log_usage
from .usage import (bar_color, fetch_usage, fmt_time, fmt_when, forecast, parse_rows, parse_time, same_window,
    short_error)
from .winapi import u32


class DataMixin:
    # data
    def refresh(self, why="timer"):
        now = time.time()
        if self.busy or now < self.blocked_until:   # (the service asked us to wait: even on a restart)
            return
        if not os.environ.get(FAKE_USAGE_ENV) and usage.login_expired():
            # the login ran out: don't ask at all (a few 401s in a row earn an hour-long "slow down").
            # data_tick checks again as soon as claude code renews it
            usage.LAST.clear()
            usage.LAST.update(status="expired")
            self.fetch_why, self.fetch_gap = why, now - self.last_fetch if self.last_fetch else None
            self.busy = True
            self.inbox.put((None, usage.LOGIN_EXPIRED))
            return
        if now - self.last_fetch < MIN_FETCH_GAP and not os.environ.get(FAKE_USAGE_ENV):
            return   # asked a moment ago (a restart, "check now", a renewed login): the tick tries again later
        self.fetch_why, self.fetch_gap = why, now - self.last_fetch if self.last_fetch else None
        self.last_fetch = now
        self.req_times = [t for t in self.req_times if now - t < 3600] + [now]
        self.busy = True
        threading.Thread(target=lambda: self.inbox.put(fetch_usage()), daemon=True).start()

    def rate_message(self):
        at = datetime.datetime.fromtimestamp(self.blocked_until)
        return (f"rate limited: the usage service asked us to slow down, so it'll try again at {fmt_time(at)}. "
                "Your last numbers are still shown.\n\n"
                "Nothing is broken, and this solves itself: it's the usage service's own cooldown, which it puts "
                "on logins that check often. It only affects the mascot's checks, not your Claude plan or Claude "
                "Code, and the mascot picks up again by itself once the wait is over.")

    def retry_note(self, err, note):
        # adds when it'll try again to the first part of an error (before any how-to-fix steps)
        head, sep, steps = err.partition("\n\n")
        return f"{head} {note}{sep}{steps}"

    @staticmethod
    def at(t):
        return datetime.datetime.fromtimestamp(t)

    def idle(self, now=None):
        # nothing has used tokens for a while, so checks slow down
        return (now or time.time()) - self.last_usage > IDLE_AFTER_MIN * 60

    def expected_gap(self, now=None):
        # seconds between checks right now: the setting, or slower when idle or after a recent "slow down"
        now = now or time.time()
        gap = self.poll.get() * (2 if now - self.limited_at < SLOW_AFTER_LIMIT else 1)
        return max(gap, IDLE_POLL_SECONDS) if self.idle(now) else gap

    def poll_gap(self, now):
        # seconds to the next check: the setting, or slower when nothing has used tokens for a while
        gap = self.expected_gap(now)
        return gap * random.uniform(0.9, 1.1)   # (a little jitter, so checks don't land in a fixed rhythm)

    def usage_log_line(self, now, ok, rows):
        # what one check looked like, for data/pet_usage.log: when it was, how often we'd been asking, what came back
        last = usage.LAST
        gap = f"{self.fetch_gap:.0f}s" if self.fetch_gap is not None else "first"
        parts = ["ok" if ok else str(last.get("status") or "fail"), f"why={self.fetch_why}", f"since_last={gap}",
                 f"req10m={sum(1 for t in self.req_times if now - t < 600)}", f"req1h={len(self.req_times)}",
                 f"up={(now - self.started) / 60:.0f}m", f"poll={self.poll.get()}s",
                 f"idle={'yes' if self.idle(now) else 'no'}"]
        if ok:
            parts += [f"{r['key']}={r['pct']:.0f}" for r in rows[:2]]
        else:
            if last.get("headers"):
                parts.append("headers=" + ",".join(last["headers"]))
            if last.get("body"):
                parts.append(f'body="{last["body"][:200]}"')
            if last.get("failed"):
                parts.append(f"failed={last['failed']}")   # (the kind of connection error, when there was no answer)
        return " ".join(parts)

    def take_result(self):
        try:
            data, err = self.inbox.get_nowait()
        except queue.Empty:
            return
        now = time.time()
        self.busy = False
        ok_rows = parse_rows(data) if usage.looks_right(data) else []
        if data is not None and not usage.looks_right(data):
            # the undocumented usage api changed shape. say so (and log what it sent: names only, never values)
            if not self.shape_logged:
                self.shape_logged = True
                names = sorted(map(str, data))[:40] if isinstance(data, dict) else [type(data).__name__]
                log_error("the usage service's answer looks different. it had: " + ", ".join(names))
            data, err = None, usage.SERVICE_CHANGED
        if data is not None:
            self.data, self.error = data, None
            self.checks_ok += 1
            self.updated = datetime.datetime.now()
            for r in parse_rows(data):
                prev = self.seen.get(r["key"])
                if prev is None or prev[0] != r["pct"] or not same_window(prev[2], r["resets"]):
                    self.seen[r["key"]] = (r["pct"], now, r["resets"])
                if r["key"] == "five_hour":
                    if self.last_5h is not None and self.last_5h >= 15 and r["pct"] <= self.last_5h - 15:
                        self.celebrate = 3    # the 5-hour limit just reset. party.
                        self.tally("resets")
                        self.say(self.pick(RESET_LINES), force=True)
                        self.play("chime")
                        if self.last_5h >= 90:
                            self.toast("Claude usage: 5-hour limit reset", "Fresh limits. Back to work!")
                    elif self.last_5h is not None and r["pct"] > self.last_5h and not self.first_result:
                        self.note_usage(now, self.poll.get() + 10)   # chat or other apps are using tokens
                    self.last_5h = r["pct"]
                self.check_milestone(r)
                self.check_pace(r)
            self.first_result = False
            self.limited = self.failed = 0
            self.last_ok = now
            self.blocked_until = 0.0
            self.next_at = now + self.poll_gap(now)
            self.remember(now, parse_rows(data))
            log_usage(self.usage_log_line(now, True, ok_rows))
            self.save()
        else:
            login = ("login expired", "login refused", "access denied")
            if err.startswith(login) and not (self.error or "").startswith(login):
                self.say("I can't see your usage anymore. hover me for how to log back in!", force=True)
                self.toast("Claude pet: " + short_error(err), "Hover the mascot for step-by-step help logging back in.")
            if err.startswith("rate limited"):
                # asked to slow down: wait 15, 30, 60 minutes, or longer if the service says so. quick retries
                # keep the throttle alive (others saw it ask for 50-60 minutes)
                self.limited += 1
                wait = max(usage.RETRY_AFTER, min(RATE_LIMITED_MAX, RATE_LIMITED_SECONDS * 2 ** (self.limited - 1)))
                self.next_at = self.blocked_until = now + wait
                self.limited_at = now
                err = self.rate_message()
                log_usage(self.usage_log_line(now, False, []) + f" retry_after={usage.RETRY_AFTER}s waits={wait:.0f}s "
                          f"in_a_row={self.limited}")
                self.save()
            elif err.startswith(("login expired", "login refused")):
                # nothing to gain from asking again with the same login: a renewed one wakes it straight away
                # (data_tick watches the file). a real 401 waits a long while, since 401s in a row earn a 429
                local = usage.LAST.get("status") == "expired"
                if not (local and (self.error or "").startswith("login expired")):
                    log_usage(self.usage_log_line(now, False, []) + " (error: " + short_error(err)
                              + (", not asked" if local else "") + ")")
                self.next_at = now + (self.poll.get() if local else REFUSED_RETRY_SECONDS)
                if not local:
                    err = self.retry_note(err, f"It'll try again at {fmt_time(self.at(self.next_at))}, or as soon "
                                               "as Claude Code renews the login.")
            else:
                # anything else. a refusal (403 and such) or a redirect won't fix itself in minutes, so it waits
                # like a 401. a server error, a timeout or an odd answer backs off (2, 4, 8, then every 15
                # minutes), so an outage doesn't turn into a steady stream of requests that ends in a "slow down"
                self.failed += 1
                status = usage.LAST.get("status")
                if isinstance(status, int) and 300 <= status < 500:
                    wait = REFUSED_RETRY_SECONDS
                else:
                    wait = min(ERROR_RETRY_MAX, self.poll.get() * 2 ** (self.failed - 1))
                self.next_at = now + wait
                err = self.retry_note(err, f"It'll try again at {fmt_time(self.at(self.next_at))}.")
                log_usage(self.usage_log_line(now, False, []) + " (error: " + short_error(err) + ")"
                          + f" waits={wait:.0f}s in_a_row={self.failed}")
            self.error = err
            self.checks_failed += 1

    def remember(self, now, rows):
        # keeps a history of the 5-hour and weekly % for the plan tab's chart:
        # every check for the last 6 hours, then one per 10 minutes, for 8 days
        by_key = {r["key"]: r["pct"] for r in rows}
        if "five_hour" not in by_key and "seven_day" not in by_key:
            return
        self.history.append((now, by_key.get("five_hour"), by_key.get("seven_day")))
        kept, last_old = [], 0.0
        for h in self.history:
            if now - h[0] > 8 * 86400:
                continue
            if now - h[0] > 6 * 3600:
                if h[0] - last_old < 600:
                    continue
                last_old = h[0]
            kept.append(h)
        self.history = kept

    def check_milestone(self, r):
        lines = MILESTONES.get(r["key"])
        if not lines:
            return
        reached = [lvl for lvl in lines if r["pct"] >= lvl]
        known = self.milestones.get(r["key"])
        if known is None or not same_window(known[0], r["resets"]):
            # first time we see this window: remember what's already passed, quietly
            self.milestones[r["key"]] = [r["resets"], reached if known is None else []]
            if known is None:
                return
        said = self.milestones[r["key"]][1]
        new = [lvl for lvl in reached if lvl not in said]
        if new:
            self.say(lines[max(new)], force=True)
            self.play("chime")
            if max(new) >= 90:
                self.toast(f"Claude usage: {NICE.get(r['key'], r['label'])} at {r['pct']:.0f}%", lines[max(new)])
            if 100 in new:
                self.tally("full_5h" if r["key"] == "five_hour" else "full_week")
            said.extend(new)

    def check_pace(self, r):
        # once per window: a heads-up when this pace runs out well before the reset, while there's time to slow down
        early = PACE_WARN.get(r["key"])
        if not early or not self.pace_warn.get() or r["pct"] < early[1] or r["pct"] >= 90:
            return
        known = self.pace_warned.get(r["key"])
        if known and same_window(known, r["resets"]):
            return
        fc = forecast(r["key"], r["pct"], r["resets"], datetime.datetime.now(datetime.timezone.utc))
        reset = parse_time(r["resets"])
        if not fc or fc[1] is None or reset is None or reset.timestamp() - fc[1] < early[0]:
            return
        self.pace_warned[r["key"]] = r["resets"]
        out = datetime.datetime.fromtimestamp(fc[1])
        line = self.pick(PACE_LINES[r["key"]]).format(when=fmt_when(out, r["key"]),
                                                     reset=fmt_when(reset.astimezone(), r["key"]))
        self.say(line, force=True)
        self.toast(f"Claude usage: {NICE.get(r['key'], r['label'])} limit running out early",
                   f"At this pace you'll hit 100% around {fmt_when(out, r['key'])}. "
                   f"It resets {fmt_when(reset.astimezone(), r['key'])}.")

    def data_tick(self):
        self.take_result()
        now = time.time()
        stamp = self.creds_changed_at()
        if stamp != self.creds_mtime:   # claude code just renewed your login: check again straight away
            self.creds_mtime = stamp
            if self.error and not self.error.startswith("rate limited"):
                self.next_at = now
                self.why_next = "login renewed"
        if self.last_ok and not self.error and self.next_at > self.last_ok + self.expected_gap(now) \
                and now - self.last_usage <= IDLE_AFTER_MIN * 60:
            self.next_at = self.last_ok + self.expected_gap(now)   # woke up from idle: back to the normal pace
        if not self.busy and now >= self.next_at:
            self.refresh(self.why_next)
            self.why_next = "timer"
        if now - self.saved_at >= 60:
            self.save()
        if self.details.visible:
            self.details.draw()
            self.details.to_front()   # another always-on-top window may have opened over it
        self.root.after(1000, self.data_tick)

    def check_keys(self):
        while True:
            try:
                kind, val = self.keys.get_nowait()
            except queue.Empty:
                return
            if kind == "thread":
                self.hotkey_tid = val
            elif kind == "registered":
                if not self.keys_paused:
                    self.bind_ok = val
                    if not all(val.values()):
                        log_error("a keyboard shortcut is already used by another app")
                    if self.settings.win is not None and self.settings.tab == "shortcuts":
                        self.settings.draw()   # shows "another app uses this" under that shortcut
            elif self.hotkeys.get() and val == 1:   # show or hide the pet (ctrl + alt + P unless changed)
                self.user_hidden = not self.user_hidden
                self.check_fullscreen()
            elif self.hotkeys.get() and val == 2:   # pin or close the details (ctrl + alt + D unless changed)
                if self.details.visible:
                    self.details.hide()
                elif not self.hidden:
                    self.details.show(pinned=True)
            elif self.hotkeys.get() and val == 3:   # come over here (ctrl + alt + H unless changed)
                self.come_here()

    def wanted_keys(self):
        # what the shortcut thread should listen for right now (nothing while switched off or recording)
        if not self.hotkeys_on or self.keys_paused:
            return {}
        return {k: v for k, v in self.binds.items() if v}

    def reregister(self):
        if self.hotkey_tid:
            u32.PostThreadMessageW(self.hotkey_tid, 0x8001, 0, 0)

    def hotkeys_changed(self):
        # off really lets go of the keys, so other apps can use them
        self.hotkeys_on = self.hotkeys.get()
        self.reregister()
        self.changed()

    def pause_keys(self, paused):
        # while you're typing a new shortcut in settings, the old ones mustn't catch the keys
        self.keys_paused = paused
        self.reregister()

    def set_key(self, name, combo):
        self.binds[name] = combo
        self.reregister()
        self.save()

    def reset_keys(self):
        self.binds = {k: list(v) for k, v in DEFAULT_KEYS.items()}
        self.reregister()
        self.save()

    def ui_tick(self):
        # 10 times a second: hover, shortcuts. twice a second: full screen. every second: moods.
        now = time.time()
        self.check_keys()
        self.outside_tick()
        self.popup.watch()
        if self.music and (self.state != "dance" or not self.sounds.get() or self.hidden or "dance" in self.muted):
            self.stop_music()
        self.check_hover(now)
        if now >= self.next_fs_check:
            self.next_fs_check = now + 0.5
            self.check_fullscreen()
        if self.platforms.get():   # quicker while it's up on a window, flying, or has windows close by
            busy = self.plat is not None or not self.grounded() or self.held or self.near
            if now - self.plats_at >= (0.2 if busy else 0.5):
                self.update_platforms()
        elif self.plat is not None or self.near:
            self.plat, self.near = None, []
        if now >= self.next_slow_check:
            self.next_slow_check = now + 1
            self.check_away()
            self.mood_tick(now)
            if now - self.screens_at >= 5:
                self.refresh_screens()
            self.tray_tick()
        if self.autohide:
            self.taskbar_tick()   # an auto-hiding taskbar slides up and down: ride along on it
        self.redraw()
        self.root.after(100, self.ui_tick)

    def shown_rows(self):
        rows = parse_rows(self.data) if self.data else []
        by_key = {r["key"]: r for r in rows}
        picks = [by_key[k] for k in ("five_hour", "seven_day") if k in by_key] or rows[:2]
        return picks[:1] if self.bubble_mode.get() == "5h" else picks

    def stale_for(self):
        # minutes since the last good answer, if checks have been missed (not just the slow idle ones)
        if not self.data or not self.last_ok:
            return 0
        age = time.time() - self.last_ok
        return int(age // 60) if age > max(STALE_MIN * 60, 3 * self.expected_gap()) else 0

    def bubble_segments(self):
        old = self.stale_for()
        segs = [(f"{SHORT.get(r['key'], r['label'])} {r['pct']:.0f}%", DIM if old else bar_color(r["pct"]))
                for r in self.shown_rows()]
        limits = len(segs)
        if old:
            segs.append((f"{old}m old" if old < 120 else f"{old // 60}h old", DIM))
        elif segs and self.idle():
            segs.append(("idle", IDLE_C))   # the numbers are fine, just checked less often
        if self.error:
            segs.append(("!" if segs else short_error(self.error), RED))
        ctx = self.bubble_context()
        if ctx is not None:   # next to the limits, so "idle", "old" and "!" stay on the right
            segs.insert(limits, (f"ctx {ctx:.0f}%", bar_color(ctx)))
        return segs or [("...", DIM)]

    def bubble_bars(self):
        old = self.stale_for()
        bars = [(SHORT.get(r["key"], r["label"][:4]), round(r["pct"]), DIM if old else bar_color(r["pct"]))
                for r in self.shown_rows()]
        ctx = self.bubble_context()
        return bars + ([("ctx", round(ctx), bar_color(ctx))] if ctx is not None else [])

    def bubble_context(self):
        # how full the latest claude code chat is, if it's switched on and the chat replied lately
        info = self.cc.context_info() if self.bubble_mode.get() == "all" else None
        if info is None or time.time() - info["when"].timestamp() > CONTEXT_FRESH_MIN * 60:
            return None
        return info["pct"]

    def warn_level(self):
        # 0 = fine (or warnings switched off), 1 = yellow ring, 2 = red ring, 3 = completely used up
        if not self.warn.get():
            return 0
        top = max([r["pct"] for r in self.shown_rows()] or [0])
        if top >= 100:
            return 3
        return 2 if top >= self.panic_at.get() else 1 if top >= self.warn_at.get() else 0

    def full(self):
        return any(r["pct"] >= 100 for r in self.shown_rows())
