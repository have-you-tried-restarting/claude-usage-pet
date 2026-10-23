# reading claude code's local logs for token counts, costs and stats (only numbers and chat names, never message text).
import datetime
import gzip
import json
import os
import random
import re
import time
from collections import Counter
from pathlib import Path

from .config import APP_PROJECTS, CC_CACHE, CC_LOGS, CC_SCAN_SECONDS, CONTEXT_WINDOWS
from .storage import log_error
from .usage import parse_time


# api list prices, dollars per million tokens: (model id starts with, input, output, cache read).
# cache writes cost 1.25x input (5 minute cache) or 2x input (1 hour cache). first match wins.
# these are what the same tokens would cost on the api. on a subscription plan you don't pay them.
PRICES = [("claude-opus-5-5", 4, 20, 0.20), ("claude-opus-5", 5, 25, 0.50), ("claude-opus-4", 5, 25, 0.50),
          ("claude-fable-5-1", 10, 50, 0.25), ("claude-fable-5", 10, 50, 1.00), ("claude-mythos", 10, 50, 0.25),
          ("claude-sonnet-5", 2, 10, 0.20), ("claude-sonnet-4", 3, 15, 0.30),
          ("claude-haiku-5", 0.10, 0.50, 0.01), ("claude-haiku-4", 1, 5, 0.10)]


def answer_cost(a):
    # api-price dollars for one logged answer, or None for a model we don't have a price for
    price = next((pr for pr in PRICES if a[2].startswith(pr[0])), None)
    if price is None:
        return None
    _, pin, pout, pread = price
    cw1h = a[7] if len(a) > 7 else 0
    return (a[3] * pin + a[4] * pout + (a[5] - cw1h) * 1.25 * pin + cw1h * 2 * pin + a[6] * pread) / 1e6


def norm_path(p):
    # one spelling per folder: git bash logs /c/Users/..., everything else C:\Users\...
    p = str(p or "")
    if re.match(r"/[a-zA-Z](/|$)", p):
        p = p[1].upper() + ":/" + p[3:]
    return os.path.normpath(p) if p else "?"


def is_scratch(path):
    # the claude app's folderless chats run in a made-up folder like scratch-2026-10-16-2777e4
    return re.fullmatch(r"scratch-\d{4}-\d\d-\d\d-[0-9a-f]+", Path(path).name) is not None


def app_names():
    # {folder (lowercase): name} for the projects named in the claude app, read fresh so a rename there shows
    try:
        d = json.loads(APP_PROJECTS.read_text(encoding="utf-8"))
        return {os.path.normpath(t["target"]["cwd"]).lower(): str(t["name"])
                for acc in d["byAccount"].values() for t in acc.get("presets", [])
                if isinstance(t.get("target"), dict) and t["target"].get("cwd") and t.get("name")}
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return {}


def exists(p):
    try:
        return Path(p).exists()
    except OSError:
        return False


def project_folder(cwd, known, moves):
    # the project a folder belongs to: the top of its git repo if it's in one, else (for a folder that's
    # gone) the nearest other folder sessions worked in above it. a gone folder that a session carried on
    # from somewhere else (renamed, moved, or a chat moved into a folder) follows it there.
    seen = set()
    while True:
        p = Path(cwd)
        if exists(cwd):
            cwd = str(next((q for q in (p, *p.parents) if exists(q / ".git")), p))
        else:
            up = [k for k in known if cwd.lower().startswith(k.lower().rstrip("\\") + "\\")]
            cwd = max(up, key=len) if up else cwd
        nxt = moves.get(cwd.lower())
        if nxt is None or cwd.lower() in seen or (exists(cwd) and not is_scratch(cwd)):
            return cwd
        seen.add(cwd.lower())
        cwd = nxt


def named(rows, titles, moves):
    # rows with the folder swapped for the name to show: the claude app's name for the project if it has one,
    # else the folder's name. a folderless chat shows its own name.
    names, known = app_names(), {a[8] for a in rows}
    label = {}   # folder -> name, or None for a chat (named per session)
    for c in known:
        f = project_folder(c, known, moves)
        label[c] = None if is_scratch(f) else names.get(f.lower()) or Path(f).name or "?"
    return [a[:8] + (label[a[8]] or titles.get(a[1]) or "Untitled chat",) for a in rows]


def fmt_money(d):
    return f"${d:,.2f}" if d < 1000 else f"${d:,.0f}"


# rough sizes in tokens (about 1.3 per word), for the fun comparison in the claude code tab
BOOKS = [("The Little Prince", 22_000), ("Alice in Wonderland", 35_000), ("Animal Farm", 40_000),
         ("The Great Gatsby", 61_000), ("Frankenstein", 98_000), ("the first Harry Potter book", 100_000),
         ("1984", 116_000), ("The Hobbit", 124_000), ("Pride and Prejudice", 160_000), ("Dracula", 210_000),
         ("Jane Eyre", 240_000), ("Moby-Dick", 270_000), ("Ulysses", 345_000), ("A Game of Thrones", 390_000),
         ("Anna Karenina", 460_000), ("Don Quixote", 500_000), ("The Count of Monte Cristo", 610_000),
         ("The Lord of the Rings", 625_000), ("Les Misérables", 700_000), ("Infinite Jest", 710_000),
         ("War and Peace", 760_000), ("Atlas Shrugged", 840_000), ("the complete Sherlock Holmes", 850_000),
         ("the whole Bible", 1_000_000), ("the complete works of Shakespeare", 1_150_000),
         ("all seven Harry Potter books", 1_400_000), ("Remembrance of Things Past", 1_650_000),
         ("the first five A Song of Ice and Fire books", 2_200_000), ("the Mahabharata", 2_400_000),
         ("the whole Wheel of Time series", 5_700_000), ("the Encyclopaedia Britannica", 57_000_000),
         ("all of English Wikipedia", 6_000_000_000)]

# ---- claude code's local logs ----

def fmt_tokens(n):
    if n < 1000:
        return str(n)
    for div, unit in ((1e9, "B"), (1e6, "M"), (1e3, "k")):
        if n >= div:
            return f"{n / div:.1f}".rstrip("0").rstrip(".") + unit


def pretty_model(m):
    # "claude-opus-5-5" -> "Opus 5.5", "claude-3-5-haiku-20241022" -> "Haiku 3.5"
    parts = [p for p in m.replace("claude-", "").split("-") if not (p.isdigit() and len(p) >= 8)]
    words = [p.capitalize() for p in parts if not p.isdigit()]
    nums = [p for p in parts if p.isdigit()]
    return " ".join(words) + (" " + ".".join(nums) if nums else "")


def hour_label(h):
    return f"{h % 12 or 12} {'AM' if h < 12 else 'PM'}"


def compare_line(tokens):
    fits = [(name, size) for name, size in BOOKS if tokens >= 2 * size]
    if fits:
        # one of the biggest few it beats by a sensible margin, the same all day so the line doesn't flicker
        near = [f for f in fits if tokens / f[1] <= 40] or fits[-1:]
        name, size = random.Random(f"{datetime.date.today()} {tokens // 1000}").choice(near[-6:])
        return f"You've used ~{tokens / size:.0f}× more tokens than {name}."
    if tokens >= BOOKS[0][1]:
        return f"That's about as many tokens as {BOOKS[0][0]}."
    return f"That's {100 * tokens / BOOKS[0][1]:.0f}% of {BOOKS[0][0]} so far."


def build_stats(answers, lines, real=None, hour_lines=None):
    # the claude code tab's numbers, for all time, 30 days and 7 days.
    # hour_lines = the lines peak hour is worked out from (each message once, not the copies in resumed logs)
    # real = each answer once. the cost estimate always uses that, whichever way tokens are counted.
    real = answers if real is None else real
    hour_lines = lines if hour_lines is None else hour_lines
    today = datetime.date.today()
    by_day = Counter()
    for a in answers:
        by_day[a[0].date()] += a[3] + a[4] + a[5] + a[6]
    today_cost = sum(c for a in real if a[0].date() == today and (c := answer_cost(a)) is not None)
    out = {"today": by_day.get(today, 0), "today_cost": today_cost, "heat": dict(by_day), "ranges": {}}
    for name, days in (("all", None), ("30d", 30), ("7d", 7)):
        since = None if days is None else today - datetime.timedelta(days=days - 1)
        A = [a for a in answers if since is None or a[0].date() >= since]
        L = [ln for ln in lines if since is None or ln[0].date() >= since]
        models, parts = Counter(), [0, 0, 0, 0]
        for a in A:
            for i in range(4):
                parts[i] += a[3 + i]
            if not a[2].startswith("<"):   # skip claude code's made-up "<synthetic>" entries
                models[a[2]] += a[3] + a[4] + a[5] + a[6]
        hours = Counter(ln[0].hour for ln in hour_lines if since is None or ln[0].date() >= since)
        peak = max(sorted(hours), key=hours.get) if hours else None   # a tie: the earlier hour
        projects, proj_sessions, cost, unpriced = Counter(), {}, 0.0, False
        for a in A:
            proj = a[8] if len(a) > 8 else "?"
            projects[proj] += a[3] + a[4] + a[5] + a[6]
            proj_sessions.setdefault(proj, set()).add(a[1])
        for a in real:
            if since is None or a[0].date() >= since:
                c = answer_cost(a)
                if c is None:
                    unpriced = unpriced or not a[2].startswith("<")
                else:
                    cost += c
        out["ranges"][name] = {
            "sessions": len({ln[1] for ln in L}), "messages": len(L), "tokens": sum(parts),
            "parts": parts, "days": len({ln[0].date() for ln in L}),
            "peak": peak, "models": models.most_common(),
            "projects": [(name_, tok, len(proj_sessions[name_])) for name_, tok in projects.most_common()],
            "cost": cost, "unpriced": unpriced,
        }
    out["recent"] = recent_sessions(answers, lines, real)
    # sessions with anything between midnight and 5 am (for the pet's diary)
    out["late"] = len({ln[1] for ln in lines if ln[0].hour < 5})
    return out


def recent_sessions(answers, lines, real, keep=8):
    # the latest sessions, newest first: start, end, messages, tokens, api-price cost, project and main model
    span, msgs = {}, Counter()
    for when, sid in lines:
        a, b = span.get(sid, (when, when))
        span[sid] = (min(a, when), max(b, when))
        msgs[sid] += 1
    latest = sorted(span, key=lambda sid: span[sid][1], reverse=True)[:keep]
    want = set(latest)
    tokens, cost, proj, model = Counter(), Counter(), {}, {}
    for a in answers:
        if a[1] in want:
            n = a[3] + a[4] + a[5] + a[6]
            tokens[a[1]] += n
            proj.setdefault(a[1], Counter())[a[8] if len(a) > 8 else "?"] += n
            if not a[2].startswith("<"):
                model.setdefault(a[1], Counter())[a[2]] += n
    for a in real:
        if a[1] in want and (c := answer_cost(a)) is not None:
            cost[a[1]] += c
    return [{"id": sid, "start": span[sid][0], "end": span[sid][1], "messages": msgs[sid], "tokens": tokens[sid],
             "cost": cost[sid], "project": proj[sid].most_common(1)[0][0] if sid in proj else "?",
             "model": model[sid].most_common(1)[0][0] if sid in model else None} for sid in latest]


def fmt_minutes(seconds):
    m = max(1, round(seconds / 60))
    return f"{m} min" if m < 60 else f"{m // 60}h {m % 60:02d}m"


# claude code's tool names, as the wizard jobs the mascot shows (pet/magic.py draws them).
# tools from add-ons (mcp__...) are "mcp". thinking and compacting come from other kinds of log lines.
JOBS = {"Read": "read", "Grep": "read", "Glob": "read", "NotebookRead": "read", "LS": "read",
        "Write": "write", "Edit": "write", "MultiEdit": "write", "NotebookEdit": "write",
        "Bash": "bash", "BashOutput": "bash", "KillShell": "bash", "KillBash": "bash", "PowerShell": "bash",
        "Monitor": "bash",
        "WebFetch": "web", "WebSearch": "web",
        "Task": "agent", "Agent": "agent",
        "TodoWrite": "plan", "ExitPlanMode": "plan", "EnterPlanMode": "plan", "TaskCreate": "plan",
        "TaskUpdate": "plan", "TaskList": "plan",
        "AskUserQuestion": "ask"}


def job_for(name):
    name = str(name)
    return "mcp" if name.startswith("mcp__") else JOBS.get(name)
CHUNK = 4 * 2 ** 20   # logs are read this much at a time, so a huge log never sits in memory all at once
CACHE_VERSION = 6   # 2: project names are the repo root, not the subfolder. 3: lines copied into other logs.
                    # 4: session starts are each log's first line. 5: chat names. 6: whole folder paths, folder moves


class ClaudeCodeLog:
    # reads claude code's logs (~/.claude/projects/**/*.jsonl) a little at a time, in the background.
    # keeps only numbers: times, session ids, model names and token counts. never message text.
    def __init__(self):
        self.offsets = {}         # file -> bytes read so far
        self.seen_answers = set() # (message id, request id). each answer is logged several times.
        self.seen_lines = {}      # line id -> the log it was first seen in, so nothing is counted twice
        self.copied = {}          # log -> line ids it repeats from another log (a resumed or forked session)
        self.line_copies = []     # (local time, session) for those repeated lines (the claude app counts them too)
        self.answers = []         # (local time, session, model, input, output, cache write, cache read)
        self.copies = []          # the extra logged copies of those answers (the claude app counts them too)
        self.starts = {}          # log -> the time on its first user or assistant line (how the claude app does it)
        self.lines = []           # (local time, session) for every user and assistant line
        self.titles = {}          # session -> its name in the claude app (the one bit of text kept)
        self.log_cwd = {}         # log -> the folder its last line was in
        self.moves = {}           # folder (lowercase) -> the folder a log carried on in after it
        self.last_error = 0.0     # when a tool call last failed (for the worried face)
        self.stats = None         # summary for the panel
        self.last_growth = 0.0    # when new output tokens last appeared
        self.built_at = 0.0
        self.ready = False
        self.job = (0.0, None)    # (when, kind) of the last tool claude used that the mascot has a look for
        self.active = {}          # session -> when it last wrote something (live, since the pet started)
        self.context = None       # (time, session, tokens, model) of the newest main-chat answer: how full its context was
        self.dirty, self.saved_at = False, 0.0   # for the cache file

    def run(self):
        try:
            self.load_cache()
        except Exception:
            log_error("reading the saved claude code numbers")
            self.__init__()   # start from scratch: it just re-reads every log
        while True:
            try:
                t0 = time.perf_counter()
                self.scan()
                self.scan_ms = (time.perf_counter() - t0) * 1000   # for the performance page
                if self.dirty and time.time() - self.saved_at > 300:
                    self.save_cache()
            except Exception:
                log_error("reading claude code's logs")   # a weird log line must never stop the pet
            time.sleep(CC_SCAN_SECONDS)

    def scan(self):
        new_output, changed = 0, False
        try:
            files = list(CC_LOGS.rglob("*.jsonl"))
        except OSError:
            files = []
        for f in files:
            try:
                size = f.stat().st_size
            except OSError:
                continue
            start = self.offsets.get(str(f), 0)
            if size < start:
                start = 0   # the file was rewritten. the seen sets stop double counting.
            while size > start:   # a bit at a time, so a huge log doesn't sit in memory all at once
                try:
                    with open(f, "rb") as fh:
                        fh.seek(start)
                        chunk = fh.read(min(size - start, CHUNK))
                except OSError:
                    break
                end = chunk.rfind(b"\n")
                if end < 0:
                    if len(chunk) == CHUNK:   # one enormous line: skip it
                        nxt = self.skip_line(f, start + CHUNK)
                        self.offsets[str(f)], start = nxt, nxt
                        continue
                    break   # only half a line so far
                start += end + 1
                self.offsets[str(f)] = start
                self.dirty = True
                for raw in chunk[:end].split(b"\n"):
                    got = self.take(raw, str(f))
                    if got is not None:
                        changed = True
                        new_output += got
        if new_output and self.ready:
            self.last_growth = time.time()
        if self.stats is None or (changed and time.time() - self.built_at > 10):
            answers, copies = named(self.answers, self.titles, self.moves), named(self.copies, self.titles, self.moves)
            self.stats = {"real": build_stats(answers, self.lines),
                          "app": build_stats(answers + copies, self.lines + self.line_copies, answers, self.lines)}
            self.built_at = time.time()
        if not self.ready:
            self.save_cache()   # the first full read is the slow one: save it straight away
        self.ready = True

    def skip_line(self, f, pos):
        # where the line that's still going at pos ends (just after its newline), or the file's end
        with open(f, "rb") as fh:
            fh.seek(pos)
            while True:
                block = fh.read(CHUNK)
                if not block:
                    return pos
                i = block.find(b"\n")
                if i >= 0:
                    return pos + i + 1
                pos += len(block)

    # ---- the cache: numbers already read, so a restart only reads what's new ----
    def seen_lines_by_log(self):
        # {log: [line ids]} for the cache, so each log's path is only written once
        out = {}
        for uid, log in self.seen_lines.items():
            out.setdefault(log, []).append(uid)
        return out

    def save_cache(self):
        t = lambda d: round(d.timestamp(), 3)
        row = lambda a: [t(a[0])] + list(a[1:])
        data = {"v": CACHE_VERSION, "logs": str(CC_LOGS), "offsets": self.offsets,
                "seen_answers": [list(k) for k in self.seen_answers], "seen_lines": self.seen_lines_by_log(), "copied": {k: list(v) for k, v in self.copied.items()},
                "answers": [row(a) for a in self.answers], "copies": [row(a) for a in self.copies],
                "starts": {k: t(v) for k, v in self.starts.items()}, "lines": [[t(w), s] for w, s in self.lines],
                "line_copies": [[t(w), s] for w, s in self.line_copies], "titles": self.titles,
                "log_cwd": self.log_cwd, "moves": self.moves,
                "context": self.context and [t(self.context[0]), *self.context[1:]]}
        tmp = CC_CACHE.with_name(CC_CACHE.name + ".tmp")
        try:
            with gzip.open(tmp, "wt", encoding="utf-8") as fh:
                json.dump(data, fh, separators=(",", ":"))
            os.replace(tmp, CC_CACHE)
        except OSError:
            log_error("saving the claude code numbers")
        self.dirty, self.saved_at = False, time.time()

    def load_cache(self):
        # picks up where the last run left off. if any log it knew got shorter or disappeared, it starts over,
        # so deleted logs drop out of the stats like before.
        try:
            with gzip.open(CC_CACHE, "rt", encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError, EOFError):
            return
        if not isinstance(data, dict) or data.get("v") != CACHE_VERSION or data.get("logs") != str(CC_LOGS):
            return
        offsets = {str(k): int(v) for k, v in data["offsets"].items()}
        for path, off in offsets.items():
            try:
                if Path(path).stat().st_size < off:
                    return
            except OSError:
                return
        when = lambda ts: datetime.datetime.fromtimestamp(float(ts)).astimezone()
        row = lambda a: (when(a[0]), str(a[1]), str(a[2]), *(int(v) for v in a[3:8]), str(a[8]))
        answers, copies = [row(a) for a in data["answers"]], [row(a) for a in data["copies"]]
        lines = [(when(w), str(s)) for w, s in data["lines"]]
        self.starts = {str(k): when(v) for k, v in data["starts"].items()}
        self.seen_answers = {tuple(k) for k in data["seen_answers"]}
        self.seen_lines = {uid: log for log, uids in data["seen_lines"].items() for uid in uids}
        self.copied = {log: set(uids) for log, uids in data["copied"].items()}
        self.line_copies = [(when(w), str(s)) for w, s in data["line_copies"]]
        self.titles = {str(k): str(v) for k, v in data["titles"].items()}
        self.log_cwd = {str(k): str(v) for k, v in data["log_cwd"].items()}
        self.moves = {str(k): str(v) for k, v in data["moves"].items()}
        ctx = data.get("context")   # (older caches don't have it)
        self.context = (when(ctx[0]), str(ctx[1]), int(ctx[2]), str(ctx[3])) if ctx else None
        self.answers, self.copies, self.lines, self.offsets = answers, copies, lines, offsets
        self.saved_at = time.time()

    def context_info(self):
        # the newest chat: {pct, window, tokens, when, session}, or None
        if self.context is None:
            return None
        when, session, tokens, model = self.context
        # shortcut: the window is guessed from the model (the logs don't say). fine until a model's default changes.
        window = next((n for start, n in CONTEXT_WINDOWS if model.startswith(start)), 200_000)
        window = window if tokens <= window else 1_000_000
        return {"pct": 100 * tokens / window, "window": window, "tokens": tokens, "when": when, "session": session}

    def usage_curve(self, start, end):
        # claude code's token use between two times as a running total, roughly weighted by what each
        # kind of token costs (output most, cache reads least), for estimating the chart's early part
        pts = sorted((a[0].timestamp(), a[3] + 5 * a[4] + 1.25 * a[5] + 0.1 * a[6])
                     for a in list(self.answers) if start <= a[0].timestamp() <= end)
        out, total = [], 0.0
        for ts, w in pts:
            total += w
            out.append((ts, total))
        step = max(1, len(out) // 150)   # no need for more than ~150 points
        return out[::step] + out[-1:] if out else []

    def take(self, raw, log=""):
        # one log line from the log file `log` -> output tokens it added (None if it was nothing new)
        try:
            d = json.loads(raw)
        except ValueError:
            return None
        if not isinstance(d, dict):
            return None
        if self.ready and (d.get("subtype") == "compact_boundary" or d.get("isCompactSummary")):
            self.job = (time.time(), "compact")   # the conversation is being shortened
        if d.get("type") == "custom-title" and isinstance(d.get("customTitle"), str) and d.get("sessionId"):
            if self.titles.get(d["sessionId"]) == d["customTitle"]:
                return None   # (logged again and again)
            self.titles[d["sessionId"]] = d["customTitle"]
            return 0
        if d.get("type") not in ("user", "assistant"):
            return None
        uid = d.get("uuid")
        when = parse_time(d.get("timestamp") or "")
        if when is None:
            return None
        when = when.astimezone()   # your local time
        session = d.get("sessionId") or "?"
        cwd, prev = norm_path(d.get("cwd")), self.log_cwd.get(log)
        if cwd != "?":   # (copied lines too: a session carried on in another folder starts with its old lines)
            a, b = (prev or "").lower() + "\\", cwd.lower() + "\\"
            if prev and not (a.startswith(b) or b.startswith(a)):   # (into or out of a subfolder isn't a move)
                # shortcut: a session that cd'd into another project and the first folder later went away
                # counts the same as a rename. good enough until someone hits it.
                self.moves[prev.lower()] = cwd
            self.log_cwd[log] = cwd
        if uid in self.seen_lines:
            # a resumed or forked session starts its log with a copy of the old one. counted once for the
            # real count, but the claude app counts every copy. (the same log read again isn't a copy)
            if self.seen_lines[uid] == log or uid in self.copied.get(log, ()):
                return None
            self.copied.setdefault(log, set()).add(uid)
            self.line_copies.append((when, session))
            self.starts.setdefault(log, when)
            m = d.get("message")
            if d["type"] == "assistant" and isinstance(m, dict) and isinstance(m.get("usage"), dict):
                self.copies.append(self.answer_row(d, m, when, session))
            return 0
        if uid:
            self.seen_lines[uid] = log
        self.lines.append((when, session))
        self.starts.setdefault(log, when)
        if self.ready:
            self.active[session] = time.time()   # this session is doing something right now
        m = d.get("message")
        if d["type"] == "user" and isinstance(m, dict) and isinstance(m.get("content"), list):
            if self.ready and any(isinstance(b, dict) and b.get("type") == "tool_result" and b.get("is_error")
                                  for b in m["content"]):
                self.last_error = time.time()   # a tool call failed
        if self.ready and d["type"] == "assistant" and isinstance(m, dict) and isinstance(m.get("content"), list):
            for b in m["content"]:   # which tool claude reached for (just its name, never what it was given)
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    self.job = (time.time(), job_for(b.get("name")))
                elif isinstance(b, dict) and b.get("type") in ("thinking", "redacted_thinking"):
                    self.job = (time.time(), "think")
        if d["type"] == "assistant" and isinstance(m, dict) and isinstance(m.get("usage"), dict):
            row = self.answer_row(d, m, when, session)
            key = (m.get("id"), d.get("requestId"))
            if key in self.seen_answers:
                self.copies.append(row)   # same answer, logged again
                return 0
            self.seen_answers.add(key)
            self.answers.append(row)
            # input + cache write + cache read is everything the model was sent: how full the chat is.
            # subagents (sidechains) have their own context, so they don't count.
            if not d.get("isSidechain") and (self.context is None or when >= self.context[0]):
                self.context = (when, session, row[3] + row[5] + row[6], row[2])
            return row[4]
        return 0

    def answer_row(self, d, m, when, session):
        # (local time, session, model, input, output, cache write, cache read, 1h cache write, folder)
        u = m["usage"]
        n = [int(u.get(k) or 0) for k in ("input_tokens", "output_tokens",
                                          "cache_creation_input_tokens", "cache_read_input_tokens")]
        cc = u.get("cache_creation") if isinstance(u.get("cache_creation"), dict) else {}
        cw1h = int(cc.get("ephemeral_1h_input_tokens") or 0)
        return (when, session, str(m.get("model") or "unknown"), *n, cw1h, norm_path(d.get("cwd")))
