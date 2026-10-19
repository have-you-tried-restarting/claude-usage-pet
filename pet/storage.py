# the settings file, the memory file and the error log.
import datetime
import json
import os
import platform
import re
import sys
import time
import traceback

from .config import (CHATTER, DEFAULT_KEYS, DEFAULT_SCALE, ERROR_LOG, ERROR_LOG_KB, FAKE_USAGE_ENV, MAX_SCALE,
    MIN_SCALE, VERSION, USAGE_LOG, USAGE_LOG_KB, PANIC_AT, PANIC_CHOICES, POLL_CHOICES, POLL_SECONDS, PROFILES, QUIET_FROM_CHOICES, QUIET_TO_CHOICES,
    BEDTIME_CHOICES, SETTINGS_FILE, SHORTCUTS, STATE_FILE, WARN_AT, WARN_CHOICES, combo_ok)
from .sounds import SOUNDS


# ---- error log ----

SEEN_ERRORS = {}   # (error type, file, line) -> how many times this run, so a ticking error doesn't flood the log


def safe_value(v):
    # numbers as they are, everything else only by type and size: never text (the token, chat lines) in the log
    if v is None or isinstance(v, (bool, int, float)):
        return repr(v)
    try:
        return f"{type(v).__name__} of {len(v)}"
    except TypeError:
        return type(v).__name__


def error_spot(e):
    # the last place in the pet's own code the error went through, and the plain values there
    tb, spot = e.__traceback__, None
    while tb:
        if os.sep + "pet" + os.sep in tb.tb_frame.f_code.co_filename:
            spot = tb
        tb = tb.tb_next
    if spot is None:
        return None, ""
    code = spot.tb_frame.f_code
    where = f"{os.path.basename(code.co_filename)}:{spot.tb_lineno} in {code.co_name}"
    names = ", ".join(f"{k}={safe_value(v)}" for k, v in spot.tb_frame.f_locals.items() if k != "self")
    return where, names


def log_error(what, exc=None):
    # writes what went wrong (with the python traceback) to data/pet_errors.log, kept small.
    # the login token is never in here: tracebacks don't include it, and values show only as numbers or sizes.
    try:
        e = exc[1] if exc else sys.exc_info()[1]
        text = "".join(traceback.format_exception(*exc)) if exc else traceback.format_exc()
        if text.strip() in ("NoneType: None", ""):
            text = ""
        if e is not None:
            where, names = error_spot(e)
            if where:
                key = (type(e).__name__, where)
                SEEN_ERRORS[key] = n = SEEN_ERRORS.get(key, 0) + 1
                if n > 1:   # the same error again: one short line on the 2nd, 4th, 8th... time, else nothing
                    if n & (n - 1) == 0:
                        what, text = f"{what}: the same {type(e).__name__} at {where} again ({n} times so far)", ""
                    else:
                        return
                else:
                    text = f"where: {where}\nvalues there: {names or '(none)'}\n{text}"
        # file paths in a traceback start with your user folder (and so your windows name). they show as ~
        # instead, so the log is safe to paste into a bug report
        home = os.path.expanduser("~")
        if len(home) > 3:   # (also the doubled-backslash way error messages print paths, any case)
            for form in (home.replace("\\", "\\\\"), home):
                text = re.sub(re.escape(form), "~", text, flags=re.IGNORECASE)
        stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        old = ERROR_LOG.read_text(encoding="utf-8") if ERROR_LOG.exists() else ""
        if len(old) > ERROR_LOG_KB * 1024:
            old = old[-ERROR_LOG_KB * 512:]   # keep the newer half
        ERROR_LOG.write_text(old + f"[{stamp}] {what} (v{VERSION}, python {platform.python_version()})\n{text}\n",
                             encoding="utf-8")
    except Exception:
        pass


def log_usage(line):
    # one line per usage check in data/pet_usage.log (times, counts and response header names only,
    # never the login token). trimmed like the error log. not written in the offline test mode.
    if os.environ.get(FAKE_USAGE_ENV):
        return
    try:
        stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        old = USAGE_LOG.read_text(encoding="utf-8") if USAGE_LOG.exists() else ""
        if len(old) > USAGE_LOG_KB * 1024:
            cut = old.find("\n", len(old) - USAGE_LOG_KB * 512)
            old = old[cut + 1:] if cut >= 0 else ""   # keep the newer half, whole lines
        USAGE_LOG.write_text(old + f"[{stamp}] {line}\n", encoding="utf-8")
    except Exception:
        pass


# ---- settings and memory files ----

DEFAULTS = {"scale": DEFAULT_SCALE, "energy": "normal", "walk": True, "jump": True, "naps": True, "anim": True,
            "bubble": "both", "bubble_style": "numbers", "bubble_ctx": True, "clock": "12h", "dates": "ddmm", "chatter": "some", "wizard": True, "warn": True, "cc_app": True, "notify": True, "sounds": False, "hotkeys": True,
            "platforms": True, "volume": 60, "muted": [], "keys": None, "settings_size": None,
            "warn_at": WARN_AT, "panic_at": PANIC_AT, "poll": POLL_SECONDS,
            "hide_fs": True, "one_monitor": False, "panel_tab": "plan", "plan_chart": "5h", "cc_view": "overview",
            "cc_range": "all", "x": None, "y": None,
            "tray": True, "pace_warn": True, "seasonal": True, "quiet_hours": False, "quiet_from": 22, "quiet_to": 7,
            "dnd": True, "rare": True, "apprentices": True, "bedtime": True, "bedtime_at": 23, "dev": False}
BOOLS = ("bubble_ctx", "walk", "jump", "naps", "anim", "wizard", "warn", "cc_app", "notify", "sounds", "hotkeys", "platforms",
         "hide_fs", "one_monitor", "tray", "pace_warn", "seasonal", "quiet_hours", "dnd", "rare", "apprentices",
         "bedtime", "dev")
CHOICES = {"energy": tuple(PROFILES), "bubble": ("both", "5h", "hover"), "bubble_style": ("numbers", "bars"), "clock": ("12h", "24h"), "dates": ("ddmm", "mmdd"),
           "chatter": tuple(CHATTER), "panel_tab": ("plan", "cc"), "plan_chart": ("5h", "7d"),
           "cc_view": ("overview", "models", "projects", "sessions"), "cc_range": ("all", "30d", "7d"),
           }


def read_json(path):
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}   # missing or broken file


def write_json(path, data):
    # write to a temp file first, then swap it in, so a crash mid-write can't leave a broken file
    tmp = path.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(data, indent=1))
        os.replace(tmp, path)
    except OSError:
        pass


def load_settings():
    saved = read_json(SETTINGS_FILE)
    st = dict(DEFAULTS)
    st.update({k: saved[k] for k in DEFAULTS if k in saved})
    try:
        st["scale"] = min(MAX_SCALE, max(MIN_SCALE, float(st["scale"])))
    except (TypeError, ValueError):
        st["scale"] = DEFAULT_SCALE
    for k in BOOLS:
        st[k] = st[k] if isinstance(st[k], bool) else DEFAULTS[k]
    for k, ok in CHOICES.items():
        if st[k] not in ok:
            st[k] = DEFAULTS[k]
    if "energy" not in saved and saved.get("walk") is False:
        st["energy"] = "statue"   # from before personalities: walking was switched off
    if isinstance(st["volume"], bool) or not isinstance(st["volume"], int) or not 0 <= st["volume"] <= 100:
        st["volume"] = DEFAULTS["volume"]
    for k, ok in (("warn_at", WARN_CHOICES), ("panic_at", PANIC_CHOICES), ("poll", POLL_CHOICES),
                  ("quiet_from", QUIET_FROM_CHOICES), ("quiet_to", QUIET_TO_CHOICES),
                  ("bedtime_at", BEDTIME_CHOICES)):
        if st[k] not in ok or isinstance(st[k], bool):
            st[k] = DEFAULTS[k]
    keys = st["keys"] if isinstance(st["keys"], dict) else {}
    st["keys"] = {name: (keys[name] if name in keys and (keys[name] is None or combo_ok(keys[name]))
                         else list(DEFAULT_KEYS[name])) for name, _, _ in SHORTCUTS}
    size = st["settings_size"]
    if not (isinstance(size, list) and len(size) == 2 and all(isinstance(v, int) and not isinstance(v, bool)
                                                               for v in size)):
        st["settings_size"] = None
    if not isinstance(st["muted"], list):
        st["muted"] = []
    st["muted"] = [k for k in st["muted"] if k in SOUNDS]
    for k in ("x", "y"):
        if isinstance(st[k], bool) or not isinstance(st[k], (int, float)):
            st[k] = None
    return st


def load_memory():
    # moods that survive a restart: when each limit last moved, pokes, milestones already said
    m = read_json(STATE_FILE)
    out = {"seen": {}, "last_5h": None, "pokes": 0, "milestones": {}, "last_usage": time.time(), "history": [],
           "greeted": "", "pace_warned": {}, "recapped": [], "log": {}, "log_since": "", "hush_until": 0.0,
           "toured": bool(m), "season_said": "", "blocked_until": 0.0,
           "last_fetch": 0.0, "limited_at": 0.0}   # (someone who already has a memory file has met the pet)
    for k in ("greeted", "log_since", "season_said"):
        if isinstance(m.get(k), str):
            out[k] = m[k]
    if isinstance(m.get("toured"), bool):
        out["toured"] = m["toured"]
    if isinstance(m.get("pace_warned"), dict):
        out["pace_warned"] = {str(k): str(v) for k, v in m["pace_warned"].items()}
    if isinstance(m.get("recapped"), list):
        out["recapped"] = [str(v) for v in m["recapped"]][-50:]
    if isinstance(m.get("log"), dict):   # the pet's diary: how many pokes, throws, jumps, dances...
        out["log"] = {str(k): v for k, v in m["log"].items()
                      if isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0}
    try:
        num = lambda v: None if v is None else float(v)
        out["history"] = [(float(h[0]), num(h[1]), num(h[2])) for h in m.get("history", [])]
    except (TypeError, ValueError, IndexError):
        pass
    try:
        out["seen"] = {k: (float(v[0]), float(v[1]), str(v[2])) for k, v in m.get("seen", {}).items()}
    except (TypeError, ValueError, IndexError, AttributeError):
        pass
    try:
        out["milestones"] = {k: [str(v[0]), [int(x) for x in v[1]]] for k, v in m.get("milestones", {}).items()}
    except (TypeError, ValueError, IndexError, AttributeError):
        pass
    for k, kind in (("last_5h", float), ("pokes", int), ("last_usage", float), ("hush_until", float),
                    ("blocked_until", float), ("last_fetch", float), ("limited_at", float)):
        try:
            if m.get(k) is not None:
                out[k] = kind(m[k])
        except (TypeError, ValueError):
            pass
    return out
