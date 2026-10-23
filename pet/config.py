# settings you can tweak: speeds, timings, limits, personalities, file locations, shortcut keys.
import os
from pathlib import Path


VERSION = "7.50"          # shown in settings > about & stats. bump it with the version in docs/PROJECT_NOTES.md.

# ---- settings ----
DEFAULT_SCALE = 1.0        # starting size. after that the size you pick in the menu is remembered.
SIZES = [0.75, 1.0, 1.25, 1.5, 2.0, 3.0]   # choices in the right-click size menu
MIN_SCALE, MAX_SCALE = 0.5, 4.0            # limits for ctrl + mouse wheel
POLL_SECONDS = 120         # how often to ask the api
ONLY_KNOWN_LIMITS = True   # show only the 5-hour and weekly limits. False shows everything the api lists.
RATE_LIMITED_SECONDS = 900 # wait at least this long after the api says "slow down", doubling each time (reports say
RATE_LIMITED_MAX = 3600    # quick retries keep the throttle alive; the service has asked for 50-60 minutes)
REFUSED_RETRY_SECONDS = 1800 # after a refusal (401, 403...), wait this long unless claude code renews the login sooner
ERROR_RETRY_MAX = 900     # other failures (server errors, timeouts) back off from the poll gap, doubling up to this
MIN_FETCH_GAP = 60         # never ask the api twice within this many seconds, whatever the reason (restarts too)
IDLE_POLL_SECONDS = 900    # when nothing has used tokens for IDLE_AFTER_MIN, check this often instead
IDLE_AFTER_MIN = 10
SLOW_AFTER_LIMIT = 3 * 3600 # after a "slow down", check half as often for this long (claude code uses the same
                           # usage service and login, so the pet only gets part of the throttle's budget)
USAGE_LOG_KB = 300         # data/pet_usage.log is trimmed to stay about this small
FAKE_USAGE_ENV = "PET_FAKE_USAGE"   # set for tests: no network. "ok" = fake numbers, "offline", or "429"
USER_AGENT = "usage-widget/0.1"
# how it moves (pixels are at 1x size)
WALK_SPEED = 28            # pixels per second
JUMP_EVERY = 30            # on average one hop every this many seconds
HOP_HEIGHT = 34            # pixels
LEAP_EVERY = 25            # on average, looks for another window to jump to this often (seconds)
LEAP_POWER = 300           # how high its legs can really take it (pixels). it sometimes thinks more.
LEAP_REACH = 520           # how far sideways a window can be before it won't bother
TASKBAR_PUSH = False       # windows pushing it while it's on the taskbar (off for now: maximized and
                           # snapped windows shoved it about when they shouldn't)
DIVE_MIN = 150             # the leap of faith needs at least this much drop below a window's edge
HAY_TIME = 1.3             # seconds it sits in the hay pile before popping out
EDGE_STUNTS = (("dive", 0.25), ("bucket", 0.15), ("bungee", 0.15), ("zipline", 0.15), ("pole", 0.15),
               ("web", 0.15))   # leaping off a window's edge: how often it's each stunt (weights): a leap of
                                # faith, a water bucket, a bungee, a zipline, a fireman's pole, a web swing
WATER_TIME = 1.0           # seconds it stands in its water before scooping it back up
# personalities (menu: personality). keep = chance it keeps walking when a walk ends, idle / walk_t = how
# long it stands about / walks (seconds), speed = walking speed, hop / leap = average seconds between random
# hops / jumps to another window, nap = nap chance multiplier. at a window's edge: edge_leap = chance it looks
# for another window to jump to, dive = chance of a leap of faith, turn = chance it turns around (else walks off).
# trips to another monitor or a high window (pet/travel.py): climb = chance at a ledge too tall to jump,
# stack = average seconds of walking between trips to a monitor above or below, high = chance it goes for a
# window too high to jump to. flip = chance it turns round when it keeps walking, roam = chance a new walk
# heads for another monitor, act = how often it does idle things (sweeping, painting...), times ACT_CHANCE.
PROFILES = {
    "parkour": {"keep": 0.9, "idle": (0.2, 0.9), "walk_t": (4, 9), "speed": 1.7, "hop": 7, "leap": 3,
                "nap": 0.05, "edge_leap": 1.0, "dive": 0.8, "turn": 0.1, "climb": 1.0, "stack": 20, "high": 0.9,
                "flip": 0.15, "roam": 0.6, "act": 0.3},
    "lively": {"keep": 0.4, "idle": (1.5, 4.5), "walk_t": (3, 6), "speed": 1.3, "hop": 18, "leap": 12,
               "nap": 0.3, "edge_leap": 0.7, "dive": 0.5, "turn": 0.4, "climb": 0.85, "stack": 50, "high": 0.6,
               "flip": 0.3, "roam": 0.3, "act": 1.0},
    "normal": {"keep": 0.0, "idle": (3, 8), "walk_t": (2, 5), "speed": 1.0, "hop": JUMP_EVERY, "leap": LEAP_EVERY,
               "nap": 1.0, "edge_leap": 0.3, "dive": 0.15, "turn": 0.5, "climb": 0.7, "stack": 90, "high": 0.35,
               "flip": 0.3, "roam": 0.0, "act": 1.0},
    "chill": {"keep": 0.0, "idle": (8, 18), "walk_t": (1.5, 3.5), "speed": 0.75, "hop": 60, "leap": 90,
              "nap": 2.0, "edge_leap": 0.1, "dive": 0.0, "turn": 0.8, "climb": 0.4, "stack": 240, "high": 0.15,
              "flip": 0.3, "roam": 0.0, "act": 1.0},
    "statue": {"keep": 0.0, "idle": (5, 10), "walk_t": (2, 5), "speed": 1.0, "hop": 10 ** 9, "leap": 10 ** 9,
               "nap": 1.0, "edge_leap": 0.0, "dive": 0.0, "turn": 1.0, "climb": 0.0, "stack": 10 ** 9, "high": 0.0,
               "flip": 0.3, "roam": 0.0, "act": 1.0},
}
PROFILE_NAMES = (("parkour", "Parkour!"), ("lively", "Lively"), ("normal", "Normal"), ("chill", "Chill"),
                 ("statue", "Statue"))
GRAVITY = 1150             # pixels per second per second
FPS = 60                   # frames a second while it moves (falls back to slower frames when idle)
MAX_STEP_UP = 400          # tallest ledge (onto a higher monitor) it will jump up
WALK_EASE = 0.3            # seconds it takes to get up to walking speed (and to slow to a stop)
# moods
SLEEP_AFTER_MIN = 5        # falls asleep when you've been away from the computer this long
NAP_CHANCE = 0.06          # chance of a short nap whenever it stops walking
WARN_AT = 80               # yellow ring around the bubble when a limit is at or above this %
PANIC_AT = 90              # ...red ring from here. both can be changed in the menu (warning levels).
WARN_CHOICES = (70, 75, 80, 85)
PANIC_CHOICES = (85, 90, 95)
HOVER_DELAY = 0.3          # seconds of hovering before the details panel shows
FADE_SECONDS = 0.18        # how long the details panel takes to fade in or out
# working and talking
CC_SCAN_SECONDS = 3        # how often to look at claude code's logs for new activity
# a chat's context size by model (first match wins, otherwise 200k). the logs don't say which window a chat has,
# so this is what the claude app showed, and anything past 200k must be the 1M one.
CONTEXT_WINDOWS = (("claude-opus-5", 1_000_000), ("claude-sonnet-5", 1_000_000))
CONTEXT_TIP_PCT = 50       # from this full, the plan tab says what /compact and /clear do
CONTEXT_FRESH_MIN = 60     # the bubble only shows the chat's context if it replied this recently
WORK_HOLD = 20             # keeps casting this long after the last sign of claude code working
IDLE_TALK_MIN = 30         # starts commenting after this long with no token usage at all
CHATTER = {"off": 0, "some": 1.0, "lots": 2.5, "max": 5.0}   # how often it talks (settings: chatter)
CHAT_GAP = (45, 120)       # seconds between bits of small talk (at "some"; "lots" divides by 2.5)
SPEAK_CPS = 30             # typing speed of speech bubbles, letters per second
ATTENTION_MIN = 20         # asks for a little attention after this long without a hover, poke or drag
# throwing, parachutes, dancing (pixels are at 1x size)
THROW_KEEP = 0.38          # share of your mouse speed a throw keeps (it's a bit heavy)
THROW_MAX = 1500           # fastest throw, pixels per second
THROW_MIN = 250            # mouse speeds below this just drop it instead of throwing
THROW_DRAG = 1.5           # air slows a throw by this fraction per second
GROUND_FRICTION = 1600     # how fast it stops sliding after landing, pixels per second per second
CHUTE_HEIGHT = 260         # opens a parachute when falling from higher than this above the floor
CHUTE_SPEED = 110          # falling speed with the parachute open, pixels per second
DANCE_CHANCE = 0.05        # chance of a little dance whenever it stops walking
ACT_CHANCE = 0.1           # ...and of something else to do: sweeping, painting, fishing, balloons, a paper plane
STALE_MIN = 10             # numbers older than this (and 3 checks) look faded in the bubble
ERROR_LOG_KB = 200         # data/pet_errors.log is trimmed to stay about this small
# keyboard shortcuts: (modifiers, key) with windows' codes. modifiers: 1 alt, 2 ctrl, 4 shift, 8 win.
SHORTCUTS = (("pet", "Show / hide the mascot", "Hides it completely (it keeps checking your usage), or brings it back."),
             ("details", "Open the details panel", "Pins the Plan / Claude Code panel open, or closes it."),
             ("come", "Call the mascot", "It comes over to your mouse, even from another monitor."))
DEFAULT_KEYS = {"pet": [3, ord("P")], "details": [3, ord("D")], "come": [3, ord("H")]}   # ctrl + alt + P / D / H
KEY_NAMES = {0x20: "Space", 0x21: "Page Up", 0x22: "Page Down", 0x23: "End", 0x24: "Home", 0x25: "Left",
             0x26: "Up", 0x27: "Right", 0x28: "Down", 0x2D: "Insert", 0x2E: "Delete"}


def key_name(vk):
    # a key's name for the screen, or None if it can't be used in a shortcut
    if 0x41 <= vk <= 0x5A or 0x30 <= vk <= 0x39:
        return chr(vk)
    if 0x70 <= vk <= 0x87:
        return f"F{vk - 0x6F}"
    if 0x60 <= vk <= 0x69:
        return f"Num {vk - 0x60}"
    return KEY_NAMES.get(vk)


def combo_parts(combo):
    # [mods, key] -> ["Ctrl", "Alt", "P"]
    mods, vk = combo
    return [n for bit, n in ((2, "Ctrl"), (1, "Alt"), (4, "Shift"), (8, "Win")) if mods & bit] + [key_name(vk)]


def combo_ok(combo):
    # a usable shortcut: a known key plus ctrl, alt or win (shift alone would get in the way of typing)
    return (isinstance(combo, list) and len(combo) == 2 and all(isinstance(v, int) and not isinstance(v, bool)
            for v in combo) and 0 < combo[0] < 16 and combo[0] & 0xB and key_name(combo[1]) is not None)
POLL_CHOICES = (120, 180, 240, 300)   # menu: refresh every (faster ones got "slow down" answers)
# pace messages (details panel)
AHEAD_BY = 10          # used% this far above the clock = "ahead of pace"
SLOW_BELOW = 0.5       # used under half of what the clock says = "way under pace"
IDLE_MIN_5H = 45       # 5-hour number unchanged this long = "not moving"
IDLE_HOURS_WEEKLY = 12 # weekly number unchanged this long = "not moving"
# early pace warning: says so once per window when the forecast runs out at least this long before the reset
PACE_WARN = {"five_hour": (30 * 60, 50), "seven_day": (12 * 3600, 40)}   # (seconds early, only from this %)
# quiet mode (menu: be quiet for an hour; settings: quiet hours)
QUIET_FOR = 3600
QUIET_FROM_CHOICES = (20, 21, 22, 23, 0)   # quiet hours start at this hour...
QUIET_TO_CHOICES = (6, 7, 8, 9)            # ...and end at this one
# bedtime (settings: pajamas at night): a striped nightcap and a candle from this hour until BEDTIME_END
BEDTIME_CHOICES = (20, 21, 22, 23, 0, 1)
BEDTIME_END = 6
# coming over when called (shortcut, tray icon, or starting the pet again)
SPRINT = 5.0               # running speed, times the walking speed
COME_DROP = 500            # further than this (or on another monitor) it parachutes in instead of running
# claude code sessions: a session counts as finished after this long with nothing new
SESSION_DONE_MIN = 8
# fun stuff
SHINY_CHANCE = 1 / 500     # chance it starts up a rare colour
UFO_HOURS = 12             # on average, a ufo visits once in this many hours you're at the computer
CAT_HOURS = 6              # ...and a cat walks past about this often
FETCH_SECONDS = 25         # the ball stays around this long after a game of fetch
# ------------------

URL = "https://api.anthropic.com/api/oauth/usage"
CONFIG_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))
CREDENTIALS = CONFIG_DIR / ".credentials.json"
CC_LOGS = CONFIG_DIR / "projects"
APP_PROJECTS = Path(os.environ.get("APPDATA", "")) / "Claude" / "ccd-session-presets.json"   # the claude app's named projects
HERE = Path(__file__).resolve().parent.parent   # the project folder (this file is in pet/)
DATA_DIR = HERE / "data"                  # everything the pet writes while it runs lives here (git ignores it)
SETTINGS_FILE = DATA_DIR / "pet_settings.json"
STATE_FILE = DATA_DIR / "pet_state.json"     # moods and memories that survive a restart
CC_CACHE = DATA_DIR / "pet_cc_cache.json.gz" # claude code's log numbers, saved so a restart doesn't re-read every log
ERROR_LOG = DATA_DIR / "pet_errors.log"
USAGE_LOG = DATA_DIR / "pet_usage.log"   # one line per usage check, to see what leads to a "slow down"
try:
    DATA_DIR.mkdir(exist_ok=True)
    # older versions kept these files next to claude_pet.py. move them in (the newer copy wins)
    # and drop a stale one, so there's never a second copy in the main folder
    for _f in (SETTINGS_FILE, STATE_FILE, CC_CACHE, ERROR_LOG):
        _old = HERE / _f.name
        if _old.exists():
            if not _f.exists() or _old.stat().st_mtime > _f.stat().st_mtime:
                _old.replace(_f)
            else:
                _old.unlink()
except OSError:
    pass
STARTUP_NAME = "Claude Usage Pet.lnk"
SUMMON_EVENT = "claude-usage-pet-summon" # starting the pet again sets this, and the running one comes over

NICE = {"five_hour": "5-hour", "seven_day": "Weekly"}
SHORT = {"five_hour": "5h", "seven_day": "wk"}
