# Claude usage pet: change log

Newest first. The spec and how everything works are in `PROJECT_NOTES.md`.

- **2026-10-20 (version 7.46): how full the current Claude Code chat is.**
  - The Plan tab has a "Context window" card under the chart: the chat's name, "13% full", a bar, and "126k of 1M tokens". From 50% full it explains what to do: /compact sums up the chat so far and carries on with room to spare, /clear starts a fresh chat, and Claude Code compacts by itself when it's nearly full.
  - The bubble shows it too ("ctx 13%", or a third bar in the bars style), next to the limits so "idle", "old" and "!" stay on the far right. It's left out once that chat hasn't replied for an hour. A new setting, Appearance > Chat context in bubble, turns it off.
  - Comes from the newest non-subagent answer in Claude Code's logs: input + cache write + cache read. The logs don't say which window a chat has, so it goes by model (Opus 5 and Sonnet 5 are 1M; anything else 200k), and anything past 200k is taken as 1M. Saved in the log cache, so it's there after a restart.
  - Tried and dropped in the same session: a separate Context tab laid out like the Claude app's context panel, with the split read from `/context` (which saves its table in the log as `contextUsage`). Back to the simple card.
  - Tested with made-up logs in a scratch folder: the newest chat wins, subagent answers are ignored, the window size comes out right, and it survives the cache. A scratch test pet (`PET_FAKE_USAGE=ok`, made-up logs) showed the card and "ctx 13%" in both bubble styles, with "idle" on the far right, and the /compact tip at 64%. Not tried in the running pet or with real chats.

- **2026-10-17 (version 7.45): warnings aren't cut off by "abra-code-abra!".**
  - A usage check where the 5-hour % went up starts the wizard, and about a second later its "starting work" line (`WORK_START`) replaced whatever the same check had just said: a milestone ("75% of the 5-hour limit used"), the pace warning or the reset line.
  - Now the starting-work line is only said when no other line is up; otherwise it's skipped (the hat still goes on).
  - Tested with a scratch test pet (`PET_FAKE_USAGE=ok`, scratch files, a made-up 40% then 82% result): the pace warning stayed up while the wizard started. With the old code the same test cut it off with "the wizard is in.". Not tried in the running pet.

- **2026-10-16 (version 7.44): a gentle ask for a star.**
  - The README says "If the pet makes you smile, a ⭐ on GitHub helps other people find it." under its first picture and at the end, and so do the release notes.
  - Settings > About's link to the repo is labelled "Star it on GitHub" instead of "View the project on GitHub".
  - `PROJECT_NOTES.md`'s GitHub section says the repo is public now and how releases are made.

- **2026-10-16 (version 7.43): the error log points at the cause.**
  - Each entry's first line ends with the pet's version and Python version, so old line numbers can be matched to the code they came from. Errors inside the pet also say what it was doing (`doing: walk`).
  - A `where:` line names the last line in the pet's own code the error went through (for example `settings_window.py:816 in draw_diary`), and `values there:` lists the values at that spot: numbers as they are, anything else only as type and size (`i=5, items=list of 2`). Text never goes in, so the login token and chat lines can't.
  - The same error again in one run is written as a single "again (N times so far)" line on the 2nd, 4th, 8th... time instead of a full traceback each time (the old log had one error nine times in 16 seconds).
  - Tested with a scratch log only (a made-up error logged 9 times, with a fake token in its values): the entry, the sizes-only values and the repeat lines came out right, and the fake token wasn't in the file. Not tried in the running pet.

- **2026-10-16 (version 7.42): fewer random "slow down" answers.**
  - Why they happened: Claude Code asks the same usage service with the same login, so the pet's 30 checks an hour share the throttle with it. A pace that worked for hours got a 429 when Claude Code asked too (two today, both at the normal 2-minute pace, `retry-after=0`).
  - Now, for 3 hours after a 429 (`SLOW_AFTER_LIMIT`), it checks half as often (every 4 minutes on the 2-minute setting; idle checks stay at 15 minutes). When it was is saved (`limited_at` in the state file), so a restart keeps the slower pace.
  - Waking up from idle and changing "Refresh every" use that slower pace too.
  - Tested offline only (no requests sent): the state file loads `limited_at`, and the gap is 240 s within 3 hours of a 429, 120 s after, 900 s when idle. Not tried in the running pet, and whether 4 minutes is slow enough is unknown until it has run for a while.

- **2026-10-16 (version 7.41): Projects shows the names you use in the Claude app.**
  - Projects past the top 5 are listed one line each in a second card (up to 10), instead of only "and 3 more".
  - Uses the Claude desktop app's own project names (`ccd-session-presets.json`), read fresh, so renaming a project in the app renames it here.
  - Renamed or moved folders: a session continued after its folder was renamed has the old and new folder in one log. The pet saves that as a move, and a folder that no longer exists counts under where work carried on. So the old "Token Tracker" sessions now count as "Claude Token Tracker".
  - A subfolder of a folder that no longer exists joins its parent (the stray "pet" entry).
  - A folderless app chat that later moved into a real folder counts there (the stray "Claude token usage desktop pet" entry).
  - Rows keep the whole folder path now. `CACHE_VERSION` 6, so the logs are re-read once.

- **2026-10-16 (version 7.40): folderless Claude app chats show their name in Projects.**
  - A session started in the Claude desktop app without a folder works in a made-up folder like `scratch-2026-10-16-2777e4`, so Projects and the sessions list showed that. Now they show the session's name from its log (`custom-title` line).
  - Only those scratch folders get renamed. Real project folders keep their folder name.
  - The names are kept in the log cache. `CACHE_VERSION` 5, so the logs are re-read once.
  - A chat whose log was deleted has no name to find, and drops out after the re-read.

- **2026-10-13 (version 7.39): a message of its own for each way a usage check can fail.**
  - Before, only "no login", "login expired", "rate limited" and "service changed" explained themselves. Every other answer showed "api error N" and every network problem "no connection (SomeError)".
  - Now each has a message in `pet/usage.py` saying what went wrong, what usually causes it and, where you can do something, how to fix it: login refused (a 401 before the login was due to run out; this used to say "login expired"), access denied (403), service not found (404, 410), request rejected (other 4xx), redirected (3xx), server error (500), service down (502, 503, 504), overloaded (529), no answer (timeout), offline (the address couldn't be looked up), secure connection failed (certificate problems), can't reach the service (refused or cut off), unreadable answer (not JSON, like a Wi-Fi sign-in page) and check failed (anything else). Each has its own short word for the bubble and tray (table in `PROJECT_NOTES.md`, under "If something goes wrong").
  - Messages for a failure that waits now end with when it'll try again.
  - Every message has two parts: what went wrong (red, as before) and, under it, what to do about it in blue, in the details panel and in Settings → Usage. When there's nothing you can do, the blue part says so: "it should solve itself" for server problems, "nothing to do on your side for now" when the service changed and the mascot needs an update. The "slow down" message's blue part is only the reassurance (its "a slower refresh setting helps" tip is gone).
  - The "slow down" message adds that nothing is broken and it solves itself: it's the usage service's own cooldown, it doesn't touch your plan or Claude Code, and the mascot carries on by itself after the wait. (Only there: the other failures have other causes, and each message names its own.)
  - Settings → Usage heads the status with what went wrong (for example "Usage service down (error 503)") instead of "Can't check right now". Login refused and access denied get the red dot, like login expired.
  - A redirect waits 30 minutes like a refusal (it was 2 minutes, doubling).
  - `pet_usage.log` notes the kind of connection error (`failed=ConnectionRefusedError`).
  - README: one line on what to do about the other bubble words.
  - Tested offline only (the network opener swapped for a fake, nothing sent): all 18 cases gave the right message, bubble word, settings heading and wait. A throwaway test pet (scratch files, `PET_FAKE_USAGE` set to `429`, then `offline`) showed the details panel with the red part and the blue part as meant. The Settings → Usage page wasn't looked at on screen.

- **2026-10-13 (version 7.38): every failed check backs off now, not just "slow down".**
  - Before, only a 429 and (since 7.37) an expired login got a longer wait. Anything else (a 403, a server error, a timeout, no connection, an answer it couldn't read) was retried every 2 minutes for as long as it lasted, the same pattern that turned 401s into an hour-long 429.
  - A refusal (any 4xx other than 429) waits 30 minutes (`REFUSED_RETRY_SECONDS`, was `LOGIN_RETRY_SECONDS`), unless the login file changes sooner.
  - Server errors, timeouts, no connection and unreadable answers wait the poll gap, then double each time (2, 4, 8 minutes), up to 15 minutes (`ERROR_RETRY_MAX`). The next good check goes back to the normal pace. `pet_usage.log` shows the wait and how many in a row.
  - Tested offline only (the network opener swapped for a fake, nothing sent): five 500s waited 120, 240, 480, 900, 900 s; a good answer reset it; timeouts did the same; a 403 and a 401 waited 1800 s. Not tested in the running pet.
  - Still out of the pet's hands: other apps using the same login's usage allowance, a PC clock that's behind (falls back to the 30-minute wait), and the service tightening its limits (the 15/30/60-minute "slow down" waits still apply).

- **2026-10-13 (version 7.37): no more "slow down" after the login runs out.**
  - Why it kept happening while idle: Claude Code's login (`expiresAt` in `~/.claude/.credentials.json`) runs out every few hours and is only renewed when Claude Code runs and needs it. The pet kept asking every 2 minutes with the old login, got 401 three times, and the fourth ask got a 429 with a 60-minute wait. An hour later the login was still old, so it happened again (seen in `pet_usage.log` on 2026-10-13 at 01:04, 10:00, 11:07 and 12:09, each starting within a minute of the login's expiry time).
  - The pet now reads `expiresAt` and doesn't send anything while the login has run out (the log says "login expired, not asked", once). It still notices a renewed login within a second and checks straight away.
  - After a real 401 (a login refused before its expiry time) it waits 30 minutes (`LOGIN_RETRY_SECONDS`, renamed `REFUSED_RETRY_SECONDS` in 7.38) instead of 2, unless the login is renewed sooner.
  - The "login expired" help says Claude Code usually renews it by itself when used in a terminal.
  - Tested offline only (a fake credentials file in a scratch folder, and the network opener swapped for one that counts calls): an expired login made no request over three checks and logged once; an in-date login that got a 401 waited 1800 s. Not tested against the real service or in the running pet.

- **2026-10-12 (version 7.36): an animated README, and the first release.**
  - Every README picture is an animated GIF now: the mascot waving as its panel fades in, the panel's tabs, the settings pages, and animated sheets of the wizard jobs, the things it does on its own, the coding jokes (two sheets) and the outfits. Recorded at 1x from a test pet (made-up numbers and projects), so they show crisp at their real size.
  - Badges under the README's title (latest release, Windows 10 / 11, Python 3.10+, no dependencies, MIT), and the download links point at the latest release.
  - A social preview card (`screenshots/social-preview.png`) for when the repo's link is shared.
  - Settings > Appearance > Seasonal outfits said "a party hat at New Year"; it's a top hat now.

- **2026-10-12 (version 7.35): sound effects are off by default.**
  - New installs start with "Sound effects" off (`sounds` in `pet/storage.py`). Existing settings files keep whatever was saved. The tip text in `pet/tips.py` says Off is the default. Not tested by running the pet.

- **2026-10-12 (version 7.34): animation fixes, new outfits, and three jokes redone.**
  - Dizzy: the stars round its head reused the drawing's `cx, cy` names, so the window's middle (and with it where its feet sit) moved while it was dizzy, and it sank half into the floor. They have their own names now.
  - Coffee: the mug's handle points back at it, in its hand, instead of away.
  - Stack overflow: thinner pancakes, so the full stack and its butter stay below the top of its head, clear of the usage bubble.
  - Seasonal outfits redrawn in the wizard hat's style (lit side, shady side, highlights, no dark edge): a ribbed, glowing jack-o'-lantern; a Santa hat with a flopped tip and bobble; a glossy top hat with confetti for New Year (it shared the birthday hat before); a polka dot party hat for its birthday; shaded hearts on springs on a headband. The nightcap got a lit edge and a shady side. No outfit gets the dark edge any more.
  - Redone from scratch with new pictures and new staging (in `pet/gags.py`, with the other jokes): digging up a 404 (an upright shovel, a growing hole and dirt pile, a clink, a treasure chest that rises and opens, a 404 page floating out), the bug hunt (a shiny beetle, a proper butterfly net with a round hoop and a mesh bag held at its middle, a dome of mesh slammed over the bug, the bug flying off on wings) and the lost semicolon (a brass detective's magnifying glass that shows the semicolon big when it passes over it; it was lying on the floor all along; a green tick when it's held up). The old sprites `BUG_A`, `BUG_B`, `BUG_C`, `SEMI` and the spade are gone.
  - Sound effects are off by default now (Settings → Sound & talking turns them on); the tip says so.
  - README pictures retaken for the jokes and the outfits.
  - Tested on a test pet (scratch files, `PET_FAKE_USAGE=ok`, made-up Claude Code logs, left monitor, 2x, plain backdrop), with screenshots through each animation: dizzy standing on the floor; the mug in its hand while held and while sipping; the full pancake stack under the bubble; every outfit on its head; the dig from the first stroke to the chest sinking back; the bug hunt's misses, catch, lift and release; the glass passing over the semicolon and showing it big, and holding it up. No errors. Not tested: sizes other than 2x, the jokes starting on their own, the bug hunt on a window ledge.

- **2026-10-12 (version 7.33): ready to go public.**
  - Security: the usage request no longer follows redirects. Python's urllib sends the `Authorization` header on to wherever a redirect points, so a redirect would have sent the login token to another site (checked with two local test servers: the old way leaked a fake token, the new one answers "api error 302" and sends nothing). `pet/usage.py` uses its own opener (`NoRedirects`).
  - Privacy: the error log replaces your user folder (and so your Windows name) with `~`, in both the normal and the doubled-backslash form, so it's safe to paste into a bug report.
  - The start-up check's "missing tkinter" pop-up says which Python it is and to install the newest one: the older Pythons from the Python install manager have no tkinter.
  - New README with pictures (all made with made-up numbers and invented Claude Code projects); new `SECURITY.md`, `CONTRIBUTING.md` (issues yes, pull requests no) and issue forms; a stricter `.gitignore` (logs, `.env`, credentials, `.claude/`, editor files).
  - Tested: the whole history for personal details and secrets (none; one author, the no-reply address); every file compiling with Python 3.10's own compiler; the start-up check on a real tkinter-less 3.10; a test pet on 3.14, 3.15 and pretending to be a 150% display (panels, settings, wizard jobs, idle activities, jokes, visitors and outfits; no errors, layouts scale cleanly); the error log scrub. Not tested: the windows on a real Python 3.10 to 3.13 with tkinter, a real scaled display, a taskbar on the side of the screen, Windows 10.

- **2026-10-11 (version 7.32): the right version in settings.**
  - Settings > About & stats said "Claude usage pet 7.0": the version there was set once in `settings_window.py` and never bumped. It's `VERSION` in `pet/config.py` now (7.32), and CLAUDE.md says to bump it along with the version in `PROJECT_NOTES.md`.
  - Tested: settings opened on a test pet (scratch files, `PET_FAKE_USAGE=ok`) shows "Claude usage pet 7.32".

- **2026-10-11 (version 7.31): settings window wide enough for the diary.**
  - Bug fix: with the settings window made narrow, the diary's "Jumps to windows" ran into its numbers ("9 made · 29 missed"). Each diary column needs about 242 px for its longest row with four-digit counts, so the window's narrowest is now 800 (was 580), and it opens 820 wide (was 720, which could also overlap). A smaller size saved from before is widened when settings opens.
  - Tested on a test pet (scratch files, `PET_FAKE_USAGE=ok`, left monitor) with a saved size of 560 and the diary at 9,999 made and 9,999 missed: settings opened at 800, couldn't be made narrower, and the row fits with a gap (screenshot).

- **2026-10-11 (version 7.30): black edge during a web swing to another monitor.**
  - Bug fix (from 7.29): during a web swing over to the next monitor, a black border showed at the right. The web swing's see-through window took its size partly from where the mascot was, so as it flew across it grew every frame, and a window resized every frame flashes its dark background at the new edge. Now its size is set once when the first web sticks, and only made bigger if the second web lands outside it.
  - Tested on a test pet (scratch files, `PET_FAKE_USAGE=ok`, left monitor), counting how often each stunt's window changed size or place: once per stunt for the web swing (across to the main monitor, on one screen, near the edge, from a low window), the zipline across monitors and the pole. No errors. I couldn't see the black edge in screenshots before the fix (it flashes between frames), so the check is that the window no longer changes size.

- **2026-10-11 (version 7.29): web swing glitches at the screen edge.**
  - Bug fix: near a screen edge the web swing jittered against the side, and could get stuck hanging tilted near the ground. Stunts kept it 46 px from the edge, but the screen clamp (`clamp_x()`) keeps it `self.half` away, and `self.half` grows to fit the speech bubble (the web swing says a line as it starts). So the clamp shoved it back in every frame while the swing or the pull down the second web dragged it out again; the pull could never reach its spot, so it stayed stuck. Now `stunt_room()` keeps at least as far from the edge as the clamp, allowing for a long line (112 px at 1x), the pull aims at a spot the clamp allows and can't take more than 2 s, and hitting the edge stops the sideways push.
  - The first web is aimed better: it never makes a swing that would scrape the floor, it stays below the top of the screen (moving nearer so it still clears the floor), and when the drop is too small for a swing at all it goes straight to the web at the ground.
  - Tested on a test pet (scratch files, `PET_FAKE_USAGE=ok`, left monitor), counting the frames where the screen clamp shoved it back: with the old margin, off a left edge near the screen's side while saying a long line, 106 frames (and the swing stuck against the edge for over 3 s); now 0. Also 0 for the web swing from a low window, off both edges, while talking, and across to the main monitor, and for the zipline, pole and bungee off a left edge. No errors.

- **2026-10-11 (version 7.28): a second web to come down with.**
  - The web swing looked odd near a screen edge: with little room it swung barely at all, let go at once and dropped a long way beside the edge. Now, when it's staying on the same screen, it lets go, then shoots a second web down at the ground a little way ahead (kept on the screen, so near the edge it's pulled back in), and is yanked down it feet first into the superhero landing, like Spider-Man. Crossing to the next monitor is unchanged.
  - Bug fix found while testing: if the screens were re-read just as it reached the ground, it could stay stuck "flying" on the floor. It now does the landing if it finds itself on the ground.
  - Tested on a test pet (scratch files, `PET_FAKE_USAGE=ok`, left monitor): off a left edge about 180 px from the screen's left side (the case that looked odd), off right and left edges with room, crossing to the main monitor, and being picked up mid-swing, with screenshots. No errors.

- **2026-10-11 (version 7.27): no shoulder straps on the bungee harness.**
  - The harness is just the belt with its buckle, and the strap down to the ring. Tested: screenshots of a bungee jump on a test pet, no errors.

- **2026-10-11 (version 7.26): bungee fix and new colours.**
  - Bug fix: during a bungee jump the usage bubble's warning ring (yellow, red or black) became huge. The harness drawing in `render.py` reused the name `ring`, which further down is the warning ring's thickness, so the ring was drawn dozens of pixels thick. It's `ring_y` now.
  - The thick part of the bungee cord is a fixed length now (it used to be the bottom fifth of the cord, so it stretched with it): a black sleeve with a metal band at the top and a clip onto the harness.
  - The cord is yellow with braid marks and a shine; the harness is black webbing with a slight sheen, a silver buckle and a silver ring.
  - Tested on a test pet (scratch files, `PET_FAKE_USAGE=ok`, left monitor) with the warning level forced to red: screenshots of the whole jump; the ring stays its normal size. No errors.

- **2026-10-11 (version 7.25): zipline, fireman's pole, web swing; a bungee harness.**
  - Three new ways off a window's edge (new `pet/stunts.py`, `StuntsMixin`): a zipline (a cable to a post near the floor, sagging under it as it rides, tilting with its legs trailing behind), a fireman's pole (it slides down hugging it, spinning, onto a red mat), and a Spider-Man web swing (a web from its raised hand, a swing, a flip and a superhero landing). Each has its lines, a sound (`zip`, `slide`, `thwip`, with on/off chips), a diary count and a dev mode chip.
  - Crossing monitors: on a window higher than the next monitor's taskbar, facing it, with "Stay on one monitor" off, it sometimes takes a zipline or web swing over to that monitor (`cross_target()`). Dev mode has "Zipline to next monitor" and "Web swing to next monitor".
  - `EDGE_STUNTS` weights: leap of faith 0.25, the other five 0.15 each.
  - Bungee: it wears a harness now (black straps, yellow stitching, a ring between its legs) and the cord hooks onto the ring. The cord used to end in the gap between its legs, so it never looked attached. The cord is thicker, blue with a yellow braid stripe and a dark edge, with a thick sleeved end at the bottom. Bug fix: off a left edge, the plank stuck out over the window instead of off the edge (a sign mistake).
  - Water bucket: the water pouring out is a thick stream now (dark edges, a light middle, wider where it lands, drips flying off).
  - Tested on a test pet (scratch files, `PET_FAKE_USAGE=ok`, left monitor, a test window from another process), with screenshots and close-ups of every phase: each new stunt off a right edge and a left edge, crossing to the main monitor by zipline and by web swing (landing on its taskbar; a plain backdrop covered that strip of the main monitor, and the test pet's "hide on full screen" was off, since the main monitor was showing something full screen), being picked up mid-stunt, dev mode for each (not counted in the diary), the zipline turning down a spot with no room for a sensible cable, the bungee off both edges with the harness, and the thicker stream. No errors. Fixed while testing: the web swing's anchor could end up off the screen, and it flew off onto the other monitor or bounced off the screen edge; the zipline tilted the wrong way; the hands grabbed the pole before reaching it; the handlebar didn't tilt with it; a zipline could have run off the bottom of a shorter monitor (they now stay on one screen unless crossing on purpose). Not tested: the new sounds by ear, sizes other than 1x, and the stunts happening on their own at a real window edge.

- **2026-10-11 (version 7.24): the bungee jump.**
  - A third way to leap off a window's edge. A plank slides out from the window's corner, it ties a bungee cord on, jumps, bounces up and down about four times hanging upside down (swinging a little), gets lowered until it's dangling just above the floor, waves, unclips, flips onto its feet and lands. The cord springs back up and the plank slides away.
  - Which stunt it does off an edge is now picked by weights: `EDGE_STUNTS` in `config.py` (leap of faith 0.4, water bucket 0.3, bungee 0.3), replacing `BUCKET_SHARE`.
  - New `pet/bungee.py` (`BungeeMixin`), `CORD_C` and `WOOD_C` in `art.py`, lines (`BUNGEE_LINES`, `BUNGEE_DONE`), a `twang` sound (on/off chip "Bungee" under Adventures), "Bungee jump" in dev mode's Moves, "Bungee jumps" in the diary. Small hooks: `turn()` hangs it along the cord, physics hands movement to `bungee_move()` while it's on the cord, and it waves while it dangles.
  - Tested on a test pet (scratch files, `PET_FAKE_USAGE=ok`, left monitor) jumping off a test window from another process: the whole jump at full speed with positions logged (lowest point 24 px above the floor, four bounces, dangling 36 px up, landing upright), screenshots of tying on, the bounces and dangling, being picked up mid-jump (the cord springs back), and playing it from dev mode (it finishes, and isn't counted in the diary). No errors. Tuned while testing: more bounces, quicker and gentler lowering (it touched the floor at first), a thicker cord, and the cord trailing a frame behind. Not tested: the `twang` sound by ear, jumping off a left edge, sizes other than 1x, and it happening on its own at a real window edge. At top speed the cord's end can still trail its feet by a few pixels.

- **2026-10-11 (version 7.23): the Minecraft water bucket jump.**
  - A new way to leap off a window's edge: when it goes for a leap of faith, 40% of the time (`BUCKET_SHARE`) it does an "MLG water bucket" instead. It hops off holding a full bucket, looks down, tips the water out just before it lands (a stream, then a source block with flowing water stepping down each side), lands in it with a splash (the bucket's empty now), stands in it a second, then scoops it back up: the bucket dips, the source block vanishes, the bucket's full again and the rest drains away. It shows off the full bucket, then puts it away. If it comes down somewhere it didn't expect before getting the bucket out, it's a bump and a "lag" excuse.
  - New `pet/bucket.py` (`BucketMixin`), the bucket picture and water colours in `art.py`, lines (`BUCKET_LINES`, `WATER_LINES`, `BUCKET_FAIL`), sounds `splash` and `bloop` (on/off chips under Adventures), "Water bucket" in dev mode's Moves, and "Water buckets" in the diary. The edge checks and the spring off the edge are shared with the leap of faith now (`edge_drop()`, `spring_off()` in movement).
  - Tested on a test pet (scratch files, `PET_FAKE_USAGE=ok`, left monitor) jumping off a test window from another process, with screenshots and close-ups of each step: holding, pouring, standing in the water, the scoop, the drain, holding the full bucket. Also: a jump where it misses the pour (ordinary landing, dizzy), being picked up while standing in the water (bucket put away, water drains), playing it from dev mode (not counted in the diary), and jumping off a left edge at 1.5x (bucket in the left hand). Fishing still works (its pond colour is also called `WATER_C`, so the Minecraft water is `MC_WATER`). No errors. Not tested: the new sounds by ear, sizes other than 1x and 1.5x, and it happening on its own at a real window edge (it was started directly).

- **2026-10-11 (version 7.22): details panel stays in front.**
  - Bug fix: the details panel (plan usage) could show up behind some windows. It was only made always-on-top once, when the pet started, so any always-on-top window opened later went in front of it. Now it's put back at the front of the always-on-top windows when it opens and every second while it's open (`to_front()` in `ui.py`, called from `Details.to_front()` and `data_tick`), without taking focus. Its tooltip and the right-click menu are put in front of it after.
  - Tested with two plain test windows (not the pet): a later always-on-top window was in front, and `to_front()` brought the first one back in front. Not tested: the real panel against real apps, or windows that use special layers (the Start menu, full-screen games), which may still go in front.

- **2026-10-11 (version 7.21): dev mode.**
  - A hidden dev mode: Ctrl + Shift + D while the settings window is open switches it on and off (saved as `dev` in the settings file). It adds a "Developer" page to settings.
  - The page can make the mascot play any animation right now (every move, idle activity, coding joke, wizard job, trip, visitor and outfit, as tap-to-play chips), or "Play all" to go through every one in a row. One it can't do from where it is is skipped, with the reason shown. A live line shows what it's doing (state, where it is, the trip).
  - New `pet/dev.py` (`DevMixin`). Small hooks elsewhere: `wizard_casting()` in movement (a dev wizard job plays even with the wizard switched off, and real Claude work waits while a dev animation plays), `job()` and `helpers()` take the dev job, render takes a dev outfit, `start_trip(..., exact=True)`, and `tally()` skips the diary while a dev animation plays.
  - For a trip, if that way goes nowhere from where it is (after one trip it's usually on the higher monitor), dev mode pops it over to another monitor's taskbar first. Without this, "Play all" could only do one trip.
  - Bug fix found with dev mode: the summoning circle (Claude Code running agents) crashed the drawing and froze the mascot, which went invisible. Version 7.17 added a second `PORTAL_C` in `art.py` (for the portals) that replaced the summoning circle's colours. The circle's colours are now `SUMMON_C`.
  - Tested on a test pet (scratch files, `PET_FAKE_USAGE=ok`, left monitor): each animation one at a time, every trip (all 11 play; the trapdoor is skipped since there's no monitor below), a trip onto a test window from another process, and every non-trip animation frame by frame with no errors. Not tested: pressing Ctrl + Shift + D for real (the switch was called directly); "Play all" from start to finish after the summoning fix; Called over and Fetch in "Play all" (they go to the mouse, so they were left out of the test).

- **2026-10-11 (version 7.20): coding jokes, and a fancier wizard hat.**
  - 14 new things it does on its own when idle, each with props, particles and programming jokes (new `pet/gags.py`, picked alongside sweeping, painting, fishing, balloons and the paper plane): a phone call from the API, a cookie (it accepts all of them), rubber duck debugging (with a lightbulb moment), coffee ("this is my Java"), a bug hunt with a net ("it's not a bug, it's a feature"), an infinite loop that makes it dizzy, a stack overflow of pancakes, counting sheep off by one, a fortune cookie, a merge conflict between two sticky notes, a recursive hand mirror, a lost semicolon found with a magnifying glass, digging up a 404 sign, and a tiny keyboard that ends in ctrl+z. Lines are in `lines.py`; pictures and colours in `art.py`.
  - The usage bubble moves up when something is over its head during an activity (`act_room`, `gag_room`).
  - New sounds `ring`, `crunch`, `typing` (a new "Coding jokes" group of on/off chips), and "Coding jokes" in the diary.
  - The wizard hat is more detailed: lit and shaded sides, a crescent moon, a star and twinkles, a bent tip, a buckle on the band and a two-tone brim (`HAT_COLOURS`, used everywhere the hat is drawn). It's 23 blocks wide (was 24) with the cone and brim centred in it, so it sits centred on the head; the first version leaned to the right.
  - Tested: every joke on a test pet (scratch files, `PET_FAKE_USAGE=ok`, left monitor) with screenshots once a second; every joke run start to finish facing both ways at 1x, 1.5x and 2x (no errors). Fixed while testing: props too small, the bulb, loop arrow, mirror and sticky notes hidden behind the usage bubble, the bug hunt wandering too far, and the found semicolon invisible on a light wallpaper. Not tested: the new sounds by ear.

- **2026-10-11 (version 7.19): smoother light on the haystack.**
  - The haystack had straight up-and-down lines in its shading: each spot was lit by whichever lump was nearest (a hard seam where that switched), and mostly by how far across it was. Now the light comes from how the outline slopes at that spot (rising faces the light, falling away is in shade), counts most near the top, uses a smooth blend of the two lumps so the dip is a soft crease, and a light checker blends one shade into the next (`hay.py`).
  - Tested: screenshots of a leap of faith on a test pet (scratch files, `PET_FAKE_USAGE=ok`, left monitor) with the tall lump on each side, zoomed in.

- **2026-10-11 (version 7.18): a proper haystack, and fixes to the hook, jetpack and boxes.**
  - The grappling hook now bites on the actual corner of the higher taskbar (just past the screen edge), and the rope drapes over that corner and hangs straight down into its hand. Before, the hook hung in the air beside the edge. The rope is drawn as a path of straight bits now.
  - The jetpack is strapped on: a frame behind it, the tanks right against its sides, shoulder straps and a belt with a buckle (the tanks used to float beside it).
  - The box tower is uneven (each box a little off to one side, wider or narrower) and the boxes are more detailed (shady side, lid seam, tape, and at random a shipping label, "this way up" arrows, a hand hole or extra tape). Tumbling boxes still turn; stacked ones stay straight, because a slight tilt looked jagged in blocks.
  - The haystack is new (`pet/hay.py`): an Assassin's Creed style plump pile with two lumps (a taller and a lower one, either way round), lit and shaded, straw strokes, swaying stray straws and a soft shadow. It pops up below as the dive starts, squashes and wobbles on landing, the mascot rises until its eyes peek over the lumps, and when it hops out the pile puffs away and a few straws stay stuck on its head. The usage bubble moves up to make room.
  - Tested: screenshots on a test pet (scratch files, `PET_FAKE_USAGE=ok`, left monitor) of the rope up to the main taskbar (zoomed on the hook), the jetpack in flight, the box tower, and leaps of faith off a test window with the tall lump on each side; the layout and window simulation again (no failures). Not tested: the haystack at display scaling above 100%.

- **2026-10-11 (version 7.17): more ways up, onto high windows too, and walking with weight.**
  - Seven new ways to get somewhere it can't jump to: a ladder that unfolds, a magic beanstalk, a tower of cardboard boxes, a jetpack, a UFO ride, a cannon and a wizard's teleport. Each has its own particles (dust, smoke, sparks, leaves, flames), none has a dark edge, and anything that moves has a speed curve: flights speed up, slow into corners and stop gently (wings and balloons too now), climbs go in eased steps.
  - Trips onto windows: when it can see a window too high to jump to, it may get up there another way (rope, ladder, beanstalk, boxes, wings, jetpack, balloons, UFO, cannon, portal, teleport), from the taskbar or from another window. The trip stops if the window moves or closes.
  - Nothing depends on one monitor layout: every trip is worked out from where the monitors and windows are when it sets off. Checked in a simulation on nine layouts (the portrait monitor where it is now, moved lower, on the right, a landscape monitor higher up, a monitor stacked above, above and offset, below, above at 150% scaling, and one too tall to climb beside) with every way, plus window trips: all landed where they should.
  - The grappling hook was upside down: now the prongs are on top and the rope ties to the ring at the bottom.
  - Things away from the mascot are drawn on one see-through "stage" window per trip (`Stage` in `sprites.py`) instead of separate sprites, so smoke and dust stay where they were made.
  - Bug fixes found while testing: climbs were never picked for side trips (the climbing spot came out 2 px outside the allowed range); the stage didn't come back after being parked off screen, and Tk sometimes held back moving it (props drawn in the wrong place), so it now shrinks in place and moves with `move_window`.
  - Walking has a little weight: it speeds up over 0.3 s and slows to a stop (`WALK_EASE`, `walk_v`).
  - Personalities: Parkour! is almost always on the move (keeps walking 90% of the time, short pauses, a window jump about every 3 s, always climbs, heads for other monitors, fewer idle activities); every personality now sets how keen it is on trips. Hovering a personality in Settings shows a tooltip explaining it, in the same style as the panel's tooltips (now one shared `Tooltip` in `ui.py`).
  - New sounds `boom`, `jet`, `thud` (on/off chips under Adventures) and new lines.
  - Tested: the simulation above; screenshots on a test pet (scratch files, `PET_FAKE_USAGE=ok`, left monitor) of the ladder, beanstalk, boxes (stacking and toppling), cannon, jetpack, UFO, teleport and rope (the new hook); the personality tooltip; a 3-minute simulation of each personality. Not tested: a real stacked monitor, a real window trip on screen (only simulated windows), real display scaling above 100%, and the new sounds by ear.

- **2026-10-11 (version 7.16): getting between monitors.**
  - The mascot can now reach a taskbar that's too high to jump to (like a portrait monitor beside the main one, whose taskbar is lower), and visits monitors stacked above or below. New `pet/travel.py` (`TravelMixin`). Five ways: a grappling hook and rope (side trips up), little wings, a portal gun (blue and orange portals), a bunch of balloons, and a trapdoor in the taskbar (down to a monitor below, then the usual parachute). Details in PROJECT_NOTES ("Monitor trips").
  - At a ledge taller than `MAX_STEP_UP` it now goes another way 70% of the time (`CLIMB_CHANCE`) instead of always turning around. With a stacked monitor, it thinks about going there about every 90 s of walking (`STACK_TRIP_EVERY`). `stacked()` in `screens.py` finds those screens.
  - Window jumps, taskbar-to-window jumps, leaps of faith and walking off onto a lower monitor are unchanged: a trip moves the mascot itself and never lands on windows.
  - Drawing: `render.py` can cut the body off at a floor line (sinking into a portal or trapdoor), hides the usage bubble while climbing and while sunk in the floor, and makes room above the head for the balloons.
  - New sounds `clink`, `flap`, `zap` (each with an on/off chip under Adventures), new lines, and "Monitor hops" in the diary.
  - Bug fix: with no Claude Code sessions in the logs at all, the welcome-back line crashed the pet on start-up (`fun.py`, `welcome`).
  - Tested on a test pet (scratch files, `PET_FAKE_USAGE=ok`, "Hide during full screen" off for the test because something was full screen on the left monitor), with each trip forced and screenshots: rope, wings, balloons and portals from the portrait left monitor up to the main taskbar; and, with the left monitor split into two pretend stacked monitors, wings, balloons and portals up, and trapdoor, wings and portals down. Also walking into the ledge on its own (it picked wings), the random stacked trip on its own (balloons), being grabbed off the rope, and being hidden mid-portal (props cleaned up each time). Not tested: a real monitor above or below (only the pretend one), display scaling other than 100%, monitors with different scaling on one trip, and the new sounds by ear.

- **2026-10-11 (version 7.15): the tooltip looks like the panel.**
  - The idle tooltip is now a small rounded card in the panel's card colour, with a bold "Idle" title and the explanation in grey under it, Segoe UI like everything else (was a square dark label with a border). Tooltip text is written "Title: explanation" and split there.
  - Tested: screenshot on a test pet (scratch files, `PET_FAKE_USAGE=ok`, left monitor) with a pretend mouse move. Not tested: a real mouse hover.

- **2026-10-11 (version 7.14): idle tooltip, and peak hour matches the app.**
  - The idle explanation line under the panel's "idle · updated ..." line is gone again. Hovering that line now shows it as a tooltip instead. The panel has a small tooltip helper (`tips`, `hover()`, `show_tip()`, `hide_tip()`).
  - Peak hour (app count): worked out from Claude Code GitHub issues (#65775, #83678). The app counts each log file once at the local hour of its first user or assistant line, all-time whatever the range. The pet used the earliest time in each session and followed the range. Now it does it the app's way; a tie keeps the hour that reached the top first. The real count (setting off) still uses the busiest message hour. Log cache `CACHE_VERSION` 4, so the logs are re-read once.
  - Tested: the log reader on this computer's real logs (numbers only), from scratch, from its cache and re-reading everything: peak hour 5 PM (same as the app), the other numbers unchanged. The tooltip on a test pet (scratch files, `PET_FAKE_USAGE=ok`, left monitor) with a pretend mouse move and a screenshot. Not tested: a real mouse hover, and how the tie rule holds up as more sessions are added (it's a best guess from one tie).

- **2026-10-11 (version 7.13): Claude Code numbers match the app again, and a tidier panel.**
  - Bug fix: with "Count tokens like the Claude app" on, Messages and Total tokens were lower than the app (4,483 and 968.7M against 6,120 and 1.3B). A resumed or forked session copies the old conversation into its new log, and the pet skipped those lines because it had seen their ids before; the app counts them. Now a line seen again in a different log counts as a copy (the same log read again still doesn't). The real count (setting off) is unchanged. The log cache format changed (`CACHE_VERSION` 3), so the first start re-reads every log once.
  - Peak hour still doesn't match (app 5 PM, pet 10 PM). None of the ways tried gave 5 PM, so it's left as it was (see "Claude Code token counts").
  - The panel's "next check in" shows minutes and seconds ("next check in 14m 46s"; under a minute, just seconds).
  - The Plan and Claude Code buttons at the top of the panel are the same width (`segmented(..., equal=True)`).
  - While idle, the panel shows the explanation under the "idle · updated ..." line, in lavender. The Claude login card in Settings keeps its line too.
  - Tested: the log reader on this computer's real logs (numbers only) from scratch, from its cache, and re-reading every log from the start: the same numbers each time (app count 16 sessions, 6,153 messages, 1.26B tokens; real count unchanged). Screenshots (test pet, scratch files, `PET_FAKE_USAGE=ok`, left monitor) of the Plan tab while idle and the Claude Code overview. Not tested: a session resumed while the pet is running, the panel while not idle.

- **2026-10-11 (version 7.12): idle has its own colour.**
  - Idle is now lavender (`IDLE_C = "#b48cff"` in `art.py`; the blue, orange, green and red are all taken). The bubble's "idle", the panel's "updated ... · next check in" line (which now starts with "idle ·" instead of ending in "(idle)") and the idle line on the Claude login card all use it. `Details.heading()` takes an optional colour for its right-hand text.
  - Tested (test pet, scratch files, `PET_FAKE_USAGE=ok`, left monitor): screenshots of all three while idle. Not tested: the panel line going back to grey when idle ends.

- **2026-10-11 (version 7.11): idle mode you can see, and no false "old".**
  - The percentages on the panel's 5-hour and Weekly rows are now the same size as the "5-hour limit" / "Weekly limit" labels (were bigger).
  - "old" in the bubble now allows for idle checks: numbers only count as old after 3 missed checks at the current pace (45 minutes while idle, as before otherwise). Before, it said "10m old" while idle even though the 15-minute wait was by design. New `idle()` and `expected_gap()` in `data.py`.
  - Idle shows: a grey "idle" after the numbers in the bubble, "(idle)" after the panel's "next check in", and a line under "Next check in" on the Claude login card explaining it.
  - Tested (test pet, scratch files, `PET_FAKE_USAGE=ok`, left monitor): screenshots of the bubble, panel and login card while idle; the old/idle logic checked for active and idle with fresh and missed checks. Not tested: the screens while not idle (only the logic was checked), and the real switch in and out of idle over time.

- **2026-10-11 (version 7.10): fewer requests, a usage log, and a no-network test mode.**
  - After a "slow down" the pet now waits 15, 30, then 60 minutes (was 3, 6, 12... up to 30), or the service's `Retry-After` if longer. Other people's reports say quick retries keep the throttle alive. `RATE_LIMITED_SECONDS` = 900, new `RATE_LIMITED_MAX` = 3600.
  - New `MIN_FETCH_GAP` (60 s): the service is never asked twice within a minute, whatever the reason. The time of the last request is saved (`last_fetch` in the state file), so quitting and starting the pet again in a row can't pile up requests. Checks also get ±10% random jitter, and the idle gap went from 10 to 15 minutes.
  - New `data/pet_usage.log` (`log_usage()` in `storage.py`, trimmed to about 300 KB): one line per check with the reason (`start`, `timer`, `manual`, `login renewed`), seconds since the last check, checks in the last 10 minutes and hour, uptime, refresh setting, idle or not, and for a failure the status, the rate-limit header names and values (`retry-after`, `anthropic-ratelimit-*`, `request-id`, ...), and the first 200 characters of the error text. No login token. It can show what leads up to a "slow down", not the service's own reason.
  - New offline test mode: set `PET_FAKE_USAGE` to `ok`, `offline` or `429` and `fetch_usage()` never touches the network or the login (`fake_usage()` in `usage.py`). The testing rule is written in `PROJECT_NOTES.md` ("Where the numbers come from") and `CLAUDE.md`.
  - Researched other ways to get the plan %, including claude.ai chat. The best on paper is Claude Code's `statusLine` `rate_limits` data. Written up in "Rate limits" in `PROJECT_NOTES.md`. A test status line never ran in the desktop app's Code tab (settings restored afterwards), so it wasn't built.
  - Tested, all offline (a safety net made any real request abort the test): the three fake modes, the log writer and its trimming, the 60-second gap, the log line for a 429, the jitter range. Not tested: the whole pet running with these changes, or against the real service.

- **2026-10-11 (version 7.9): fewer checks, and a "slow down" wait that survives restarts.**
  - When the usage service says "slow down", the wait is now saved (`blocked_until` in `pet_state.json`). Restarting the pet used to check straight away and could get limited again; now it shows the rate-limit message and waits. "Check now" and changing "Refresh every" also respect it.
  - Idle polling: if nothing has used tokens for 10 minutes, it checks every 10 minutes instead of every 2 to 5. It returns to the normal pace as soon as Claude Code's logs or the plan % show tokens going up. New in `config.py`: `IDLE_AFTER_MIN`, `IDLE_POLL_SECONDS`.
  - Why: the usage service once asked for a ~1 hour wait. The cause wasn't found (the error log has no rate-limit entries); fewer requests and no restart skipping are the likely helpers, not a proven fix.
  - Tested: it compiles; the saved wait loads back; the idle and active gaps (120s vs 600s); refresh does nothing while waiting. Not tested against the real service, or on the running pet until it's restarted.

- **2026-10-11 (version 7.8): subfolders no longer show up as their own projects.**
  - The Projects view named a project after the last folder in the session's working directory, so a session that worked in `pet/` or `docs/` showed up as a separate project. `cclog.project_name()` now walks up to the folder that has `.git` and uses that name (falling back to the plain folder name outside a repo). Results are cached per folder.
  - `CACHE_VERSION` went to 2, so the log cache is rebuilt once on the next start and old rows get the new names.
  - Tested: the name lookup (repo root, two subfolders, no folder, a missing folder, a non-repo folder). Not tested on the running pet until it's restarted.

- **2026-10-10 (version 7.7): one copy of the data, fewer pictures.**
  - Copies of the data files left in the main folder are now always cleaned up on start: if the main-folder copy is newer than the one in `data/`, it replaces it; if it's older, it's deleted. Before, a leftover copy stayed forever once `data/` had its own. (These leftovers came from a pet still running the pre-7.6 code, which writes to the main folder until it's restarted.)
  - Screenshots: only the wizard jobs sheet is kept, moved to `screenshots/wizard-jobs.png`. The other README pictures and `docs/jobs/` are removed, and the README no longer shows them.
  - Tested: the move/cleanup logic in a scratch folder (newer root copy, older root copy, no data copy). Not tested on the running pet until it's restarted.

- **2026-10-10 (version 7.6): tidier folder.**
  - The change log moved out of `PROJECT_NOTES.md` into `docs/CHANGELOG.md`, so the notes are quicker to read.
  - The notes (`PROJECT_NOTES.md`, `LOCAL_NOTES.md`) moved into `docs/`. `README.md`, `CLAUDE.md` and `CLAUDE.local.md` stay in the main folder.
  - Everything the pet writes (`pet_settings.json`, `pet_state.json`, `pet_cc_cache.json.gz`, `pet_errors.log`) now lives in `data/`, made on first run. `config.py` has `DATA_DIR` and `ERROR_LOG`; `storage.py` imports `ERROR_LOG` from there. On start, any old copies next to `claude_pet.py` are moved into `data/` once. `.gitignore` just lists `data/`.
  - Removed the unused `OPTIMIZE_PROMPT.md` and the `usage_widget_pos.json` ignore line (nothing writes it).
  - Messages that mentioned `pet_errors.log` now say `data/pet_errors.log`.

- **2026-10-10 (version 7.5): no more slumping at 100%, and pajamas at bedtime.**
  - At 100% the mascot no longer sits still, slumped with tired eyes. It walks, hops, dances and does its idle activities as usual. The black ring and the occasional 100% line stay. (One line, "I'm exhausted. clocking out until the reset.", was swapped for one that fits.) The "tired" eyes are gone from the drawing code.
  - New: Pajamas at bedtime (Settings → Appearance → Mascot), on by default from 11 PM until 6 AM: a striped nightcap and a candle (see "Pajamas at bedtime" above). "Bedtime from" (8 PM to 1 AM) only shows while the toggle is on.
  - Tested (test pet, scratch files, left monitor, 3x, bedtime forced on): screenshots awake (cap, candle in hand, rays) and asleep (cap, candle on the floor), heading left and heading right; the on/off hours for 8 PM, 11 PM, midnight and 1 AM. Not tested: the settings rows on screen (they use the same show/hide as Apprentices), the bedtime line, and it switching on by itself at the real hour.

- **2026-10-10 (version 7.4): fixed the memory leak on Python 3.15.**
  - The pet kept using more memory the longer it ran (about 1 MB every 4 seconds, faster during rune rain). Python 3.15 comes with Tk 9.0, and Tk 9.0 leaks a little memory (around 80 bytes) for every canvas item that's deleted, whatever kind it is (rectangles, lines, polygons, ovals, text; images don't). The pet redraws everything up to 60 times a second by deleting all items and making new ones, so it leaked all the time. Rune rain draws the most pieces per frame, so it leaked fastest. Tk 8.6 (Python 3.14) doesn't leak, and the pet's own Python memory stayed flat throughout.
  - Fix: every canvas is now `ui.Canvas`, which reuses its items. `delete("all")` only hides them (one call), and the next `create_*` of the same kind with the same option names takes a hidden one back: new coordinates, new options, shown and raised to the top, so the drawing order is the same as before. Embedded widgets (the settings search box) are still made and deleted for real. Nothing else in the drawing code changed.
  - Tested (test pets with scratch files on the left monitor, every wizard job and idle activity forced in turn for 30 s each, 3.14 and 3.15 side by side): before the fix, 3.15 grew about 95 MB in 5 minutes while 3.14 stayed flat. After it, both stay flat apart from one-off steps (the first full read of Claude Code's logs, a new font size, the 5-minute cache save). CPU and frame rate were the same on both. A screenshot of the fixed pet looked right. Not tested: the settings window and details panel over a long time (they also use `ui.Canvas` now, but only redraw when something changes).

- **2026-10-10 (version 7.3): new things to do when idle.**
  - Stargazing, the practice spell and the book are gone. In their place: sweeping, painting, fishing through a hole in the taskbar, blowing up balloons that pop, and throwing a paper plane (see "Idle activities" above). Each one is equally likely (the plane only when none is out already). `ACT_CHANCE` is unchanged.
  - The paper plane is a new little window (`Sprite`), turned to match its heading in 15° steps.
  - Particles can now fall (`"g"`), and there's a `"dot"` particle in any colour (paint, ice, splashes, balloon bits, dust).
  - The diary's three old counts are replaced by five new ones (old counts stay in `pet_state.json` but aren't shown).
  - Tested (test pet, scratch files, left monitor, plain backdrop, 1x and 2x, both sides): each activity started directly, with screenshots of each stage; the diary counts; and the plane's flight checked over many simulated throws (median about 550 px at 1x, 2–6 s in the air, about 1 in 7 loops). Not tested: them starting on their own timers, the plane bonking off screen edges on screen, and fishing or sweeping on top of a window.

- **2026-10-10 (version 7.2): three things to do when idle.**
  - Stargazing at night, a practice spell that backfires, and reading a little book (see "Idle activities" above). New Pet part: `pet/idle.py`; new lines in `pet/lines.py`; three more counts in the diary.
  - The usage bubble makes room for the hat during the practice spell, like it does for the wizard.
  - Tested (test pet, scratch files, second monitor, 2x, plain backdrop): each activity started directly, with screenshots of the feet-up stargazing with stars, moon and a shooting star, the spell before and after the poof, and the book; the diary counts; and the earlier scenarios still pass. Not tested: them starting on their own timers (a 10% chance each time it finishes standing about).

- **2026-10-10 (version 7.1): the wizard's jobs, a new-look panel, a welcome back, and lots more to say.**
  - **Details panel redone** in the Claude desktop app's style (the same palette and controls as the settings window): a Plan / Claude Code switch, sections as headings over cards, rounded bars, a chart in a dark well, the overview as six tiles in one card. Sessions moved into Claude Code, beside Overview, Models and Projects.
  - **Welcome back** on every start after the first: a greeting for the time of day, and an offer to carry on with the last Claude Code session's project.
  - **Wizard jobs** for every kind of Claude Code tool, plus thinking and shortening the conversation (see "Wizard jobs" above, and `docs/wizard-jobs.png`). New Pet part: `pet/magic.py`. The reading tome is redrawn in much more detail and floats beside the mascot now.
  - **Much more to say:** about 300 new lines across walking (42 now), quotes, curious questions, pokes, drags, throws, dances, windows, sleep, waking, jumps, work, attention, mornings and late nights, plus 26 that break the fourth wall. A new chatter level, **Non-stop** (5× as often), and it avoids its last 60 lines.
  - Tested (test pet, scratch files, made-up logs, second monitor): every job at 2x (screenshots in `docs/`), the page turn's five stages, the job each tool name maps to (including `mcp__` tools, thinking blocks and compact lines), the welcome with a made-up last project, every panel view, and CPU while working: roughly 8–18% of one core with the rune rain and 7–12% with the crystal ball across runs (each animates at about 25 frames a second; it drops back when Claude stops). The earlier scenarios still pass. Not tested: real Claude Code activity driving the jobs live.
  - **Ideas for when it's idle** (proposed, not built):
    - stargazing at night: lies on its back, little stars twinkle above
    - practising spells that go wrong: a tiny puff of smoke, singed hat
    - reading a pocket book on its own, turning a page now and then
    - fishing off the edge of a window into the taskbar
    - juggling three little pixels
    - building a tiny sandcastle out of taskbar pixels, then knocking it over
    - stretching and doing push-ups (badly)
    - chasing its own tail (it doesn't have one; it checks)
    - waving at the mouse pointer and pretending to talk to it
    - painting a little picture on an easel, then holding it up
    - a cup of tea: blows on it, sips, little steam squiggles
    - knitting a scarf that slowly gets longer over the day
    - tapping along to the system clock, or "conducting" while you type
    - peeking over the top of the window it's standing on
    - hide and seek: hides behind a window edge, peeks out when you look
    - blowing bubbles that pop on the screen edges
    - a paper aeroplane thrown off a window, landing somewhere on the taskbar
    - sleepwalking a few steps during a nap
    - writing in its diary (the Pet diary) with the quill
    - polishing its wand, or adjusting its hat in a little mirror

- **2026-10-10 (version 7.0): a big batch of improvements, quality-of-life and fun.**
  - **Technical:**
    - The usage service changing shape is spotted and explained ("service changed"), with only the names it sent written to the error log.
    - Claude Code's log numbers are cached in `pet_cc_cache.json.gz`, so a restart only reads new lines; logs are read 4 MB at a time.
    - An auto-hiding taskbar is handled: the floor follows it up and down.
    - The notes are brought up to date: the settings window's real pages, where `PRICES` lives, and an idea that was already done.
  - **Quality of life:**
    - A tray icon with your usage in its tooltip; click to call the mascot, right-click for the menu.
    - Call the mascot over with Ctrl + Alt + H, the tray icon, or by starting the pet again. It runs to your mouse or parachutes in.
    - Quiet mode: for an hour from the menu, quiet hours, and following Do Not Disturb.
    - An early pace warning when you'd run out well before the reset.
    - Session wrap-ups in a speech bubble, and a new Sessions tab recapping the latest five sessions.
    - A short tour on the very first start, replayable from settings.
  - **Fun:**
    - Seasonal outfits (Halloween, Christmas, New Year, its birthday, Valentine's Day) and New Year fireworks.
    - Its eyes follow your mouse pointer.
    - A floating spell tome while Claude reads files.
    - Apprentice wizards for parallel Claude Code sessions.
    - A pet diary counting everything it gets up to.
    - Play fetch.
    - Rare surprises: a shiny colour, a UFO abduction, and a cat (with a meow).
  - New files: `pet/fun.py`, `pet/tray.py`, `pet/sprites.py`. The settings window's version is now 7.0.

- **2026-10-10 (version 6.6): tested on Python 3.15.**
  - Python 3.15 comes with Tk 9.0 (3.14 has Tk 8.6). Ran the real pet on both, on the second monitor with scratch settings and made-up usage numbers: the pet, both details panel tabs, the settings window, speech bubbles and the menu look the same, and nothing was logged as an error. All pet files load on 3.15 with warnings turned into errors.
  - `Start pet.bat` and the startup shortcut picked up 3.15 on their own once it was installed. No code changes were needed.

- **2026-10-10 (version 6.5): tidy-up.**
  - `Start pet.bat` replaces the hand-made `Start Claude Pet` shortcut, which pointed at one Python version.
  - Removed `usage_widget.py`, the original widget kept as a backup (it's still in the git history).

- **2026-10-10 (version 6.4): easier to install for someone new.**
  - New `Start pet.bat`: double-click to start the pet with no console. It finds Python, and if there's none it explains and opens the python.org download page.
  - `claude_pet.py` checks for Windows, Python 3.10+ and tkinter before loading anything, and says what to fix in a pop-up (with a button to open the download page). If the pet crashes while starting without a console, a pop-up points to `pet_errors.log`.
  - "Start with Windows" now uses the `pyw` launcher when there is one, so the shortcut keeps working after Python updates.
  - README: a step-by-step install section for people who don't use terminals, and a short troubleshooting list.
  - Tested: the checks (old Python, no tkinter, not Windows) with fake pop-ups; `Start pet.bat` with the launcher, with only `python` on the path, and with no Python, in a folder with spaces and brackets in its name; the startup shortcut opening through `pyw`; the crash pop-up. Not tested: a real older Python, Windows 10, Microsoft Store Python, and the security prompt for a `.bat` from a downloaded ZIP.

- **2026-10-10 (version 6.3): getting ready to go public.**
  - Removed a code comment that suggested sending Claude Code's user agent. The pet always identifies itself as `usage-widget/0.1`.
  - Personal working notes moved out of `CLAUDE.md` into the gitignored `CLAUDE.local.md`. Test notes say "second monitor" instead of describing one desk.
  - Fixed an old author email in the git history so every commit uses the same GitHub address.

- **2026-10-10 (version 6.2): the code is split into small files.**
  - `claude_pet.py` (about 4,900 lines) became a 45-line starter plus the `pet/` package (20 files, mostly 100–400 lines; the biggest is the settings window at about 1,000). Nothing about how the pet looks or behaves changed. The shortcut, "Start with Windows" and the settings, memory and error-log files are all where they were.
  - The `Pet` class is split into themed parts (mixins) that combine into one class.
  - Done by a script that cut the file at its section lines and worked out each file's imports. It then checked that no line of code went missing, no name is unresolved, there are no import loops and no method is defined twice.
  - Tested old and new side by side: sounds and dance music, small talk, times and dates, the login help, shortcuts (including a real key press), the whole settings window, the details panel placement, riding and being pushed by windows, jumps, wall slaps, the leap of faith, personalities, poking, dragging, throwing, the menu and refresh. Results matched; the only differences were random ones.

- **2026-10-10 (version 6.1):**
  - Sounds are levelled to about the same loudness: each is scaled to the same average power (`SOUND_LEVEL`), not its loudest peak, and never clips. High, buzzy or hissy sounds seem louder than they measure, so the eagle cry, scream and hay are trimmed further by ear (`SOUND_TRIM`). Measured average power is now 4–7% for every sound; the eagle and scream were the loudest-sounding before. `SOUND_VERSION` is now 5.

- **2026-10-10 (version 6.0): the settings window, redesigned to look and work like the Claude desktop app's settings.**
  - **Layout:**
    - a darker sidebar on the left with icons (Windows' own Segoe MDL2 icon font) and the page names
    - on the right, the page title, then each section as a small heading over a rounded card
    - each setting has its label and description on the left and its control on the right
    - warm greys and Claude's orange
  - **Pages:**
    - Mascot (movement, behaviour)
    - Appearance (live preview, size, usage bubble, time and date)
    - Sound & talking (sound effects and volume, which sounds, chatter)
    - Usage & alerts (checking, warnings and notifications, Claude Code)
    - Shortcuts
    - System (startup, screens)
    - About & stats (Claude login, performance, about)
  - **Controls:** choices are segmented controls (the chosen option on a lighter tab inside a dark well), right beside the label when there's room, below it when there isn't.
  - **Settings that only matter sometimes stay hidden until they do:**
    - the ring levels only show while warnings are on
    - volume and the sound chips only show while sound effects are on
    - the shortcut list only shows while shortcuts are on
  - **Live previews:**
    - Appearance starts with a picture of the mascot and its bubble at the real chosen size and style, with your real numbers.
    - Each sound chip has a ▶ to hear it without switching it.
  - **Search:** a "Search settings" box at the top of the sidebar (Ctrl + F) shows every matching setting from every page, working right there, under "Page › Section" headings. Esc clears it.
  - **Login status card** on About & stats:
    - a status dot: connected, login expired, not logged in, or can't check
    - when it last checked and when it will check next
    - a "Check now" button
    - the step-by-step login help when it's needed
  - **Reset per section:** a small "Reset" beside each section heading puts just that section back to its defaults (`reset_section`).
  - **Keyboard:**
    - Tab / Shift + Tab or the arrow keys move through the pages and settings, with an orange focus ring; it scrolls into view.
    - Space or Enter switches or presses the focused setting.
    - Left / Right change choices and sliders, or play a sound chip.
    - Ctrl + F jumps to search.
  - **Saved note:** the always-there "Changes apply straight away" line is gone; a small ✓ Saved appears in the corner for a moment after each change.
  - Still resizable (now 580–1100 wide, from 420 tall up to the screen's height) and scrolls. The size is remembered.
  - Version 6.0 (`VERSION`), with a link to the project on GitHub (opens in your browser).
  - Tested: screenshots of every page, the preview at 2x, search, keyboard focus and Space switching a setting, a section reset, the saved note, the login card with an expired login, and the smallest size.

- **2026-10-10 (version 5.17):**
  - Stats: CPU, Memory and Frame rate each have a small area graph of the last 3 minutes (`PERF_POINTS` = 90 samples, one every 2 s), right under their header. The scale grows to fit; the dotted line is the top of the scale.
  - The settings window can be resized:
    - drag the bottom-right grip, the right edge or the bottom edge (the cursor shows resize arrows)
    - size limits: 370–760 wide, 400 tall up to the screen's height
    - the size is remembered (`settings_size`)
  - The title and tabs stay fixed at the top and the "Changes apply straight away" line at the bottom. The content scrolls between them with the mouse wheel, with a slim scrollbar. Tabs wrap onto a second line when the window is narrow. Every tab now uses the window's height instead of all tabs being as tall as the tallest one.

- **2026-10-10 (version 5.16):**
  - New Settings tab, Stats: live performance of the pet itself, updated every 2 seconds while open:
    - CPU (of the whole processor, and of one core)
    - memory
    - frame rate
    - usage checks ok / failed and the last check time
    - how long reading new Claude Code log lines took
    - windows watched
    - sound files on disk
    - how long it's been running
  - CPU, memory and usage checks get a green / amber / red dot. CPU and memory come from Windows' own process counters (`own_usage`, using GetProcessTimes and K32GetProcessMemoryInfo).
  - Measured in testing: about 0.1% CPU (2% of one core) and 48 MB while standing still.

- **2026-10-10 (version 5.15):**
  - Windows no longer push the mascot while it's on the taskbar (`TASKBAR_PUSH = False`): maximized and half-screen windows were shoving it about when they shouldn't. The code is still there; set it to True to bring it back. Windows still push it when it's standing on another window.

- **2026-10-10 (version 5.14):**
  - All sounds are half as loud as before at the same volume setting (`soft_all` in `make_sound`). `SOUND_VERSION` is now 4, so the quieter copies are made fresh.

- **2026-10-10 (version 5.13):**
  - Login expired / no login: the details panel now shows step-by-step help (`LOGIN_HELP`) for someone who has never used a terminal: open Command Prompt, type claude, log in through the browser, close it. The problem line is red; the steps are plain text. The speech line and notification point to the panel.
  - Times show as 3:05 PM by default, with a 24-hour option (Settings → Look → Clock).
  - Dates show as Fri 16/10 (day/month) by default, with a month/day option (Settings → Look → Dates). Used everywhere a reset time, chart label or run-out forecast is shown (`fmt_time`, `fmt_day`, `fmt_when`).
  - Saved as `clock` ("12h" / "24h") and `dates` ("ddmm" / "mmdd").

- **2026-10-10 (version 5.12):**
  - New Settings tab, Shortcuts:
    - the on/off switch (moved from System)
    - each shortcut with what it does and its keys drawn as key caps
    - click a shortcut, press new keys (Esc cancels, Backspace clears)
    - clear warnings for keys without Ctrl/Alt, keys the other shortcut uses, and keys another app has taken
    - Reset to defaults
  - Saved as `keys` in `pet_settings.json` (`[modifiers, key code]` per shortcut, or null).
  - The shortcut thread now re-registers whenever they change, lets go of them while you're typing a new one, and lets go completely when shortcuts are switched off.
  - Tested: recording, all three warnings (another app, here the already-running pet holding Ctrl + Alt + P / D), changing to Ctrl + Alt + F9 and a real key press of it hiding the pet, Backspace clearing, saving, reset, and screenshots.

- **2026-10-10 (version 5.11):**
  - Every sound can be switched on or off on its own (Settings → Sound → Which sounds).
    - Each sound is a chip: warm with a filled orange dot when on, plain with an empty ring when off.
    - Switching one on plays it, so you know which it is.
    - While the main Sound effects switch is off, the chips dim and the line above them says none of them will play.
  - Saved as `muted` in `pet_settings.json`: the list of sounds switched off, so any sound added later starts switched on.
  - Desktop notifications moved from the Sound tab to System.
  - Tested: toggling chips, the sample on switching on, saving, a muted sound not playing, and screenshots of all on, some off, and the main switch off.

- **2026-10-10 (version 5.10):**
  - The parachute sound is now a deep "floom", like a big sheet of cloth catching the air: a low rumble that swells in, flutters, and settles, with a low tone under it (it was a plain hiss). `SOUND_VERSION` is now 3.

- **2026-10-10 (version 5.9):**
  - Sound effects are on by default. A settings file saved earlier with them off keeps them off until switched on in Settings → Sound.
  - The eagle cry is longer (about 2.2 s, plus an echo): a rising "kee", a held cry, then a long falling, raspy tail.
  - Landing in hay is now a soft "tsss" of straw instead of a thump and rustle.
  - Dances last 8–12 s (were 3.5–6 s); the music loops for the whole dance.
  - Sound files now carry a version number (`SOUND_VERSION`), so changed sounds are remade instead of reusing old saved copies.
  - Note: Windows plays one sound at a time, so on a short drop the hay "tsss" cuts the eagle cry off when it lands.

- **2026-10-10 (version 5.8):**
  - New sounds, all made from maths in `make_sound` (no sound files), which now mixes several notes at once:
    - `eagle`: a raspy hawk-like screech when it takes a leap of faith.
    - `hay`: a whump and rustle when it lands in the hay.
    - `splat`: a thud and slap when it hits a window's side.
    - `spell`: a sparkly run of notes when wizard mode starts, then every 12–25 s.
    - `dance`: a 3.2 s chiptune loop (C major, 150 bpm, lead + bass + drums) that plays while it dances and stops when the dance ends.
  - The scream when thrown hard, the whoosh when the parachute opens and the boing on a bouncy landing were made but never played; they play now.
  - Sound files are made in the background at start-up and when the volume changes, so there's no hiccup the first time.
  - Windows plays one sound at a time, so any new sound cuts off the dance music.
  - Tested: every sound generated with nothing clipping (levels balanced, 24–81% peak), the dance loop starting and stopping with the dance, and the spell sound on wizard start. Not listened to by Claude.

- **2026-10-09 (version 5.7):**
  - Jumps that come up short slap into the side of the window and slide down it, instead of passing through.
  - Windows that go down behind the taskbar don't push it; it stands in front of them. Windows ending on or above the taskbar still do.

- **2026-10-09 (version 5.6):**
  - Personalities: Parkour!, Lively, Normal, Chill, Statue.
  - Livelier personalities walk more, nap less, and jump to nearby windows more often.
  - Leap of faith off window edges, landing in a pile of hay.
  - Windows push it aside on the taskbar too.

- **2026-10-09 (version 5.5):**
  - Jumps over to windows nearby. It's brave, and not always right.
  - Much chattier: small talk every minute or two at "Sometimes" (it was every 4–10 minutes), about whatever it's doing. New lines for walking, dancing, standing on windows, sleep-talking, falling off edges, jumps, plus curious questions. More lines everywhere else too, and it doesn't repeat its last 25 lines.

- **2026-10-09 (version 5.4):**
  - It follows a dragged window smoothly instead of jumping every few frames.
  - Windows in front of it are solid: they push it aside, and if it's cornered it drops through to the taskbar.
  - The screen edges are hard limits while it's riding a window.

- **2026-10-09 (version 5.3):**
  - The details panel opens below or beside the mascot when there's no room above it.
  - Smooth, steady 60 fps while moving (fixed jittery throws).

- **2026-10-09 (version 5.2):**
  - Fixed the right-click menu only working once.
  - The menu opens beside the mascot, and right-clicking again closes it.
  - Throws are heavier: small flicks just drop it, and big throws keep 38% of the mouse speed.

- **2026-10-09 (version 5.1):**
  - Removed accessories.
  - The right-click menu is now a small dark menu in the panel's style, with just Refresh now, Settings and Quit (it replaces the long Windows menu and its tooltips).
  - New settings window: panel style, five tabs, switches, pills and sliders, and a sound volume slider.

- **2026-10-09 (version 5):**
  - Error log.
  - Per-monitor scaling.
  - Old numbers fade in the bubble.
  - Cost estimate at API prices.
  - Projects view.
  - Worried face on Claude Code tool errors.
  - Desktop notifications.
  - Keyboard shortcuts (Ctrl + Alt + P / D).
  - Time-of-day behaviour.
  - Standing on (and riding) windows.
  - Unlockable accessories.
  - Optional sound effects.
  - Settings window.
  - Re-checks straight away when Claude Code renews the login.
  - README screenshots.

- **2026-10-09 (version 4.2):**
  - Fixed the dark box flash and the flicker when switching between dragged/thrown and other states: the window now never resizes or jumps.
  - The plan chart fills in the time before the pet started, estimated from Claude Code's logs (dotted).
  - Removed the 30-second and 1-minute refresh options.

- **2026-10-09 (version 4.1):**
  - Plan tab: usage chart for the current window (5-hour or Week) with the pace line, a forecast, and reset clock times.
  - Friendlier "slow down" handling: a clear message, waits that grow while it repeats, and it follows the service's `Retry-After`.
  - Fixed the dark outline flicker while it tumbles, by keeping the window one size.

- **2026-10-09 (version 4):**
  - Throwing: it keeps its speed, bounces and slides.
  - It hangs from where you grab it and swings.
  - New animations: parachute, dizzy stars, dancing with notes, wake-up stretch, slumped and tired at 100%.
  - New lines: screams, attention-seeking, bored, dizzy, parachute, and 100% lines.
  - The 100% ring is black with a silver edge.
  - "Refresh every" setting.
  - Roomier details panel with a wrapped footer, and the same height on every tab so the tabs never move.
- **2026-10-09 (version 3.3):**
  - Claude Code numbers count like the Claude desktop app by default, with an option for the real count.
  - Tooltips on every menu item.

- **2026-10-09 (version 3.2):**
  - Removed the warning sign.
  - The warning ring now also goes around the bubble's tail. It's yellow from 80% and red from 90%, and both levels can be changed in the menu ("Warning levels").

- **2026-10-09 (version 3.1):**
  - Rounded boxes are drawn with smooth corner images, so their corners are clean (anti-aliased in the panel, step-free on the mascot's see-through window).
  - The activity grid uses whole pixels, so every square is the same size.
  - Replaced the sweat drop with a warning sign plus a red ring around the bubble. It can be switched off with "Warn when nearly full".

- **2026-10-09 (version 3):**
  - Speech bubbles: encouraging and silly quotes, plus lines about work, quiet times, milestones, resets, pokes, dragging, sleeping and waking. A "Chatter" setting controls how often.
  - Wizard mode while tokens are going up: hat, wand and sparkles.
  - The bubble can show bars instead of numbers.
  - New Claude Code tab in the details panel, with real token counts from the local logs, an overview, models, and 7-day, 30-day and all-time ranges.
  - Remembers moods, milestones and pokes across restarts (`pet_state.json`).
- **2026-10-09:** Put the project in a private GitHub repo. Added `README.md` and `.gitignore`. Moved this computer's details into `LOCAL_NOTES.md`, which git ignores.
- **2026-10-09 (version 2):**
  - Hides during full screen.
  - Hovering shows the details panel, which fades and slides in and out smoothly.
  - Walks across monitors, with a "Stay on one monitor" option.
  - Higher, smoother jumps: 34 px, with lighter gravity and the exact air curve.
  - New animations: sleeping (when you're away and random naps), poke reaction with hearts, waving, glancing, sweating at high usage, celebrating resets, and wiggling legs while held.
  - Fixed: windows on a monitor to the left of the main one were placed wrongly.
  - Clicking now pokes the mascot instead of opening the details panel.
- **2026-10-09 (version 1):** Turned the panel widget (`usage_widget.py`) into the walking pet (`claude_pet.py`). Default size is 1x. Added the double-click shortcut and this notes file.
