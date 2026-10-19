# Claude usage pet: project notes

A small Claude mascot that walks along the top of the Windows taskbar. A bubble above its head shows Claude plan usage. If any file here gets lost or corrupted, this note has enough detail to rebuild it. You can give this file to Claude and ask it to rebuild the project.

Last updated: 2026-10-20 (version 7.47)

The change log is in `CHANGELOG.md`, next to this file.

## Files in this folder

| File | What it is |
| --- | --- |
| `claude_pet.py` | Starts the pet (the shortcut and "Start with Windows" point at it). Before loading anything it checks for Windows, Python 3.10+ and tkinter, and explains in a pop-up if one is missing. |
| `Start pet.bat` | Double-click to start the pet without a console window. Finds Python (the `py` launcher first, then `python`/`pythonw` on the path). If there's no Python it says so and opens python.org. |
| `.gitattributes` | Keeps `.bat` files in Windows line endings, which batch files need. |
| `pet/` | The pet's code, split into small parts. `pet/__init__.py` lists what each file does and where new things go. See "Code layout" below. |
| `README.md` | Short intro for the GitHub page. |
| `docs/PROJECT_NOTES.md` | This file. |
| `docs/CHANGELOG.md` | What changed in each version, newest first. |
| `.gitignore` | Tells git which files stay on this computer only. |
| `data/pet_settings.json` | Saved settings: size, toggles, position. Created the first time the pet runs. Safe to delete. Not on GitHub. |
| `data/pet_state.json` | The pet's memory: when each limit last moved, milestones it has already announced, how many times you've poked it, its diary, and which sessions it has wrapped up. Safe to delete (it just forgets). Not on GitHub. |
| `data/pet_cc_cache.json.gz` | Claude Code's log numbers the pet has already read (times, session ids, models, token counts, project folder names), so a restart only reads what's new. Safe to delete (it re-reads the logs). Not on GitHub. |
| `docs/LOCAL_NOTES.md` | Details about this particular computer (paths, monitors, Python install). Not on GitHub. |
| `data/pet_usage.log` | One line per usage check: when, why (timer, start, manual, login renewed), seconds since the last one, how many checks in the last 10 minutes and hour, and for a failure the status, `Retry-After`, the rate-limit header names and the short error text. For working out what leads to "slow down". Never the login token. Kept under about 300 KB. Safe to delete. Not on GitHub. |
| `data/pet_errors.log` | What went wrong, if anything (Python error details, never the login token). Kept under about 200 KB. Safe to delete. Not on GitHub. |
| `data/` | Everything the pet writes while it runs: settings, memory, the log cache and the error log. Made on first run (and old copies next to `claude_pet.py` are moved in once). Git ignores it. |
| `screenshots/` | The README's animated GIFs: `hero.gif` (it waves, then the Plan panel fades in), `panel-tabs.gif` (the panel's tabs in turn), `settings.gif` (the settings pages in turn), and animated sheets `wizard-jobs.gif`, `adventures.gif`, `coding-jokes-1.gif`, `coding-jokes-2.gif`, `outfits.gif`. Plus `social-preview.png`, the 1280x640 card GitHub shows when the repo's link is shared (uploaded in the repo's Settings > Social preview). All recorded from a test pet at 1x on a plain backdrop with `PET_FAKE_USAGE=ok`, made-up Claude Code logs (`CLAUDE_CONFIG_DIR` pointed at invented projects) and naps off (a test pet left alone falls asleep mid-joke), so nothing personal is in them. Recorded at 10 frames a second and made into GIFs by a small pure-Python encoder (a shared 256-colour palette, only the changed pixels after the first frame); the recording scripts aren't in the repo. |
| `SECURITY.md` | How to report a security problem privately, and what the pet can access. |
| `CONTRIBUTING.md` | Issues welcome; pull requests aren't accepted; rules for forks (stdlib only, the token rule, `PET_FAKE_USAGE`). |
| `.github/ISSUE_TEMPLATE/` | The bug report and idea forms (bug reports warn never to paste a token), and a link to private security reporting. Blank issues are off. |

## Code layout

The code is a package (`pet/`) started by `claude_pet.py`. Every file begins with a one-line summary and imports exactly what it uses from the others.

| File | What's in it |
| --- | --- |
| `pet/config.py` | Tweakable numbers: speeds, timings, limits, personalities (`PROFILES`), file locations, default shortcut keys. |
| `pet/lines.py` | Everything the mascot says. |
| `pet/tips.py` | The descriptions next to each setting. |
| `pet/art.py` | The mascot's pixel shapes and all colours. |
| `pet/usage.py` | Login token, the usage API call, parsing, time and date formatting, login help text. |
| `pet/cclog.py` | Claude Code's local logs: token counts, costs, stats. |
| `pet/storage.py` | The settings file (`DEFAULTS`), the memory file, the error log. |
| `pet/winapi.py` | Windows calls: monitors, windows, idle time, notifications, the shortcut thread, startup, single instance. |
| `pet/sounds.py` | Making the sound effects. |
| `pet/ui.py` | Shared drawing helpers: the `Canvas` every window uses (it reuses items, see 7.4), rounded boxes, smooth corners, fading, text wrapping. |
| `pet/mascot.py` | The `Pet` class: puts the parts below together; its settings and start-up. |
| `pet/screens.py`, `mouse.py`, `talk.py`, `data.py`, `movement.py`, `render.py`, `fun.py` | The parts of the `Pet` (mixin classes): monitors, mouse handling, talking and reactions, data and ticks, physics and movement, drawing, and the extras (being called over, quiet mode, seasons, session wrap-ups, the tour, the diary, the tray icon, fetch, rare visitors). They all share one `self`. |
| `pet/idle.py` | Things it does on its own when idle (a part of the `Pet`): sweeping, painting, fishing, balloons, a paper plane. |
| `pet/gags.py` | Coding jokes it acts out when idle (a part of the `Pet`): phone call, cookie, rubber duck, coffee, bug hunt, infinite loop, stack overflow, off by one, fortune cookie, merge conflict, recursion, lost semicolon, 404, tiny keyboard. Hooked into `idle.py`'s activities. |
| `pet/dev.py` | Dev mode (a part of the `Pet`): the list of every animation (`DEV_GROUPS`), starting any one on demand (`dev_play`), "play all" (a queue watched every 150 ms: the next starts once it's back on its feet with nothing going on, `dev_free`, or after 45 s), and the hooks other parts ask: `wizard_casting()` (movement), `dev_job` (magic `job()`, fun `helpers()`), `dev_outfit` (render), `dev_now` (fun `tally()` skips the diary). `start_trip(..., exact=True)` only goes that way. |
| `pet/hay.py` | The haystack at the bottom of a leap of faith (a part of the `Pet`): its shape and shading, popping up below the dive, the squash, and puffing away. |
| `pet/bucket.py` | The Minecraft water bucket jump (a part of the `Pet`): the other way to leap off a window's edge. The bucket, pouring it out, the water on its own stage window, standing in it, and scooping it back up. See "Leap of faith". |
| `pet/bungee.py` | The bungee jump (a part of the `Pet`): another way to leap off a window's edge. The plank and cord on their own stage window, the cord's spring physics, letting it down, unclipping. The harness itself is drawn in `render.py`. See "Leap of faith". |
| `pet/stunts.py` | More ways off a window's edge (a part of the `Pet`): a zipline, a fireman's pole and a Spider-Man web swing, and taking the zipline or web over to the next monitor. Their props on one stage window. See "Leap of faith". |
| `pet/travel.py` | Getting somewhere it can't walk or jump to (a part of the `Pet`): another monitor or a high window, by rope, ladder, beanstalk, boxes, wings, jetpack, balloons, UFO, cannon, portals, teleport or trapdoor. See "Trips". |
| `pet/magic.py` | The wizard's jobs (a part of the `Pet`): which job is on, how the mascot holds itself, the props and their particles. |
| `pet/tray.py` | The tray icon, with its own thread and hidden window. |
| `pet/sprites.py` | Small see-through windows for things that leave the mascot's side: the fetch ball and the cat. |
| `pet/details.py` | The hover details panel. |
| `pet/menu.py` | The right-click menu. |
| `pet/settings_window.py` | The settings window. |

`pet/__init__.py` also says where new things go (a new setting, animation, sound, settings page or Pet part).

One thing to know: `usage.RETRY_AFTER` changes while the pet runs, so other files read it as `usage.RETRY_AFTER`, never by importing the name on its own.

## How to use it

1. Double-click **Start pet.bat** in this folder.
2. The mascot appears on top of the taskbar. The first numbers can take a few seconds to show up.
3. **Hover** over the mascot or its bubble:
   - It waves, and after a moment the details panel fades in above it.
   - The panel looks like the Claude desktop app: warm greys, a Plan / Claude Code switch at the top, sections as small headings over rounded cards. It has two tabs:
     - **Plan:** pace bars, reset times (as countdowns and clock times), tips, a chart of your usage across the current window with the pace line (switch between 5-hour and Week), a forecast ("at this pace you'll run out around 23:40" or "you'll use about 60% by the reset"), a "Context window" card (how full the latest Claude Code chat's context is: the chat's name, "13% full" with a bar, and "126k of 1M tokens"; from 50% full, `CONTEXT_TIP_PCT`, it says what /compact and /clear do; see "Chat context" below), and Claude Code tokens used today.
     - **Claude Code:** stats read from your Claude Code logs. "Overview" shows sessions, messages, total tokens, active days, peak hour, favourite model, a 26-week activity grid and a book comparison. "Models" shows tokens per model plus the input/output/cache split. "Projects" shows the top 5 projects with bars and the rest as one line each (up to 10 more). "Sessions" is a recap of your latest 5 Claude Code sessions: project folder, when it started, how long it ran, messages, tokens, main model and the API-price estimate; one still going has an orange "Active" pill. The first three views can show 7 days, 30 days or all time.
   - Move the mouse onto the panel and it stays open, so you can click the tabs. Move away and it fades out.
   - The panel is the same height on every tab, so the tabs never move when you switch.
4. **Click** the mascot to poke it. It squishes, hops, makes a happy face and pops a heart.
5. **Drag** the mascot to pick it up. It hangs from the spot you grabbed and swings as you move. Its legs wiggle.
   - **Throw it** by letting go while moving. It keeps your speed, screams, bounces off screen edges and the floor, and slides to a stop. From high up it opens a parachute. A hard landing leaves it dizzy.
6. **Right-click** the mascot for a small menu with **Refresh now**, **Play fetch**, **Quiet for an hour** (or **Talk again** while it's quiet), **Settings** and **Quit**. It opens beside the mascot (not on top of it). A click anywhere else, or right-clicking the mascot again, closes it.
7. **Settings** opens a window laid out like the Claude desktop app's settings: a sidebar with seven pages (and a search box), and on the right each section as a card. Every option has a switch, choice buttons or a slider, plus a short description. Changes apply straight away, and a small "✓ Saved" shows for a moment. Drag the top to move it, the edges to resize it, and close it with × or Esc. Each section has its own "Reset".
   - **Mascot:** Personality (Parkour! / Lively / Normal / Chill / Statue), Take naps, Wizard when Claude works, Apprentices for parallel sessions (shown while the wizard is on), Stand on windows, Rare surprises, Animations
   - **Appearance:** a live preview, Size (slider, 0.5x–4x), Seasonal outfits, Pajamas at bedtime (with Bedtime from 8 PM–1 AM, shown only while it's on), Bubble shows (limits + context, the default / both limits / 5-hour only / on hover; "limits + context" adds "ctx 13%", or a third bar, while the latest chat replied in the last hour), Bubble style (numbers / bars), Keep details open, Clock (12 / 24 hour), Dates (day or month first)
   - **Sound & talking:** Sound effects (master switch, off by default), Volume (0–100%; plays a sample when you let go), Which sounds (every sound as an on/off chip with a ▶ to hear it: Reactions = Poke, Bounce, Scream, Wall splat; Adventures = Parachute, Eagle cry, Hay landing, Water bucket, Bucket refill, Bungee, Zipline, Pole slide, Web, Cat, Grappling hook, Wings, Portal gun, Cannon, Jetpack, Boxes; Moods = Wizard magic, Dance music, Milestones; Coding jokes = Phone, Cookies, Typing), Chatter (off / sometimes / a lot / non-stop), Quiet hours (with From 8 PM–midnight and Until 6–9 AM), Follow Do Not Disturb
   - **Usage & alerts:** Refresh every (2–5 minutes), Warn when nearly full, Yellow ring from (70–85%), Red ring from (85–95%), Early pace warning, Desktop notifications, Count tokens like the Claude app
   - **Shortcuts:** Keyboard shortcuts (on/off; off lets go of the keys so other apps can use them), then each shortcut with what it does and its keys as key caps (defaults: Ctrl + Alt + P shows or hides the mascot, Ctrl + Alt + D pins or closes the details panel, Ctrl + Alt + H calls the mascot over). Click one and press the new keys; Esc cancels, Backspace clears it. Warnings appear if the keys have no Ctrl/Alt, are already used by another shortcut, or another app already uses them.
   - **System:** Start with Windows, Tray icon, Hide during full screen, Stay on one monitor
   - **About & stats:** the Claude login card (status, last and next check, Check now, login help), the Pet diary, live Performance graphs, the version (`VERSION` in `pet/config.py`, kept the same as the version at the top of this file), a GitHub link and "Show the tour again"
   - **Developer** (hidden): press **Ctrl + Shift + D** while the settings window is open to switch dev mode on (it goes straight to this page) and again to switch it off (or "Leave dev mode" at the bottom of the page). It stays on across restarts. The page has "Play all", which plays every animation below one after another (and turns into "Stop"), and every animation as a chip you tap to play it right now, in groups: Moves (walk, hop, wave, poked, party hops, look around, stretch, worried, dizzy, dance, nap, thrown, parachute, called over, fetch, leap to a window, leap of faith, water bucket, bungee jump, zipline, pole slide, web swing, zipline to next monitor, web swing to next monitor), Idle activities, Coding jokes, Wizard (the plain wand, each job, and apprentices; it pretends Claude is working for 10 seconds, even with the wizard switched off), Trips (each way to get somewhere: to another monitor if that way works, popping it over to another monitor's taskbar first if it has to, otherwise up onto a high window), Visitors (UFO abduction, cat, shiny colours) and Outfits (each seasonal outfit and the pajamas; tap again to take it off). One it can't do from where it is says why under its group (the edge stunts need it on a window; the "to next monitor" ones need a window higher than that monitor's taskbar, the trapdoor a monitor below). At the bottom: what it's doing right now (state, where it is, the trip), and the page redraws as that changes. Nothing played from here goes in the diary.
8. **Ctrl + mouse wheel** over the mascot fine-tunes its size. This may only work after you've clicked the mascot once.
9. **Call it over** from anywhere: press Ctrl + Alt + H, click the tray icon, or start the pet again (double-click `Start pet.bat` while it's running). It runs to your mouse; if your mouse is far away, on another monitor, or it's up on a window, it parachutes in right above your mouse instead. It also comes back if it was hidden with Ctrl + Alt + P.
10. **Tray icon** (on by default, Settings → System): a little mascot by the clock with a dot in your usage colour. Hover it for your numbers, click it to call the mascot over, right-click it for the menu. Windows may put new icons in the "show hidden icons" arrow at first; drag it out onto the taskbar to keep it in view.
11. **Play fetch** (right-click → Play fetch): a red ball flies from your mouse. The mascot runs after it, picks it up and brings it back to your mouse. You can grab the ball and throw it yourself too, even while the mascot is carrying it. The ball disappears if nobody plays with it for 25 seconds.

### Things it does on its own

- **Two or more monitors:** it walks from one screen to the next. If the next screen's taskbar is lower, it drops down. If it's higher, it jumps up (up to 400 px at 1x). If it's higher than that, it usually finds another way up (how often depends on the personality), otherwise it turns around. It also visits monitors stacked above or below its own now and then, and climbs onto windows too high to jump to. Everything is worked out from where your monitors and windows are at that moment, so moving a monitor in Windows' display settings just works. The ways it gets there (details in "Trips"):
  - **Grappling hook:** whirls the hook over its head like a lasso, throws it up (prongs first) onto the edge it's going to (clink, sparks), tugs twice, climbs the rope hand over hand, hauls itself over the edge, and reels the rope back in. Going up to a higher taskbar beside it, the hook bites on the very corner of that taskbar and the rope drapes back over the corner and hangs straight down this side of the screen edge, into its hand.
  - **Ladder:** pulls out a short ladder that unfolds section by section (each one clicks into place), climbs it two rungs at a time, steps off, and pulls the ladder up after itself.
  - **Beanstalk:** pokes a bean into the floor (dirt flies), and a beanstalk shoots up with the mascot riding the big leaf on top, leaves unfurling as it grows and bits of leaf drifting off. It hops off, and the beanstalk shrinks back into the ground.
  - **Cardboard boxes:** hops, and a box slides in underneath it at the top of each hop, until the tower reaches the ledge. The tower isn't a straight column: each box sits a little off to one side and is a bit wider or narrower, and each has a shady side, the lid's edge and seam, tape, and maybe a shipping label, "this way up" arrows, a hand hole or an extra strip of tape. It hops off and the tower topples, the boxes tumbling down and squashing flat in puffs of dust.
  - **Wings:** little white wings sprout from its back and flap. It flies up (or down), over, and lands, and the wings fold away. A feather drifts off now and then.
  - **Jetpack:** strapped on: a frame behind it, a tank on each side right against its body, straps over its shoulders and a belt with a buckle. A few coughs of smoke, then a roar: flames (longer the faster it goes), sparks and a trail of smoke.
  - **Balloons:** three balloons puff up in its hand and it floats up, swaying, over to the other side, then pops them one by one and drops the last bit.
  - **UFO ride:** the saucer flies in, beams it up inside, flies it over, beams it down, and flies off while it waves.
  - **Cannon:** a cannon pops out and aims, it hops into the barrel, the fuse fizzes and the cannon trembles, then BOOM: a flash, a big puff of smoke, and it flies out tumbling (smoke trail), lands dizzy, and the cannon goes away in a puff.
  - **Portal gun:** shoots a blue portal onto the floor beside it and an orange one onto the other floor (pew, pew), hops into the blue one, sinks through the floor, and shoots up out of the orange one. The portals close behind it.
  - **Wizard's teleport:** on goes the wizard hat, sparkles swirl round it, it fades away in a burst of sparkles and fades back in over there.
  - **Trapdoor** (down to a monitor below): stomps twice, a trapdoor opens in the taskbar, it drops through, comes out of the top of the monitor below and parachutes down.
  - Turn on "Stay on one monitor" to keep it on one screen (it still climbs onto windows). You can still drag it to another screen.
- **Full screen:** when a video, game or anything else is full-screen on its monitor, it fades away. It comes back when you leave full screen. A monitor that's showing something full-screen counts as a wall, so it won't walk onto it.
- **Sleep:** if you haven't touched the mouse or keyboard for 5 minutes, it lies down, closes its eyes and floats z's. When you come back, it wakes up with a hop and a wave. It also takes short naps (20–60 seconds) now and then. Hovering or clicking wakes it up.
- **Usage warning:** when a limit reaches 80%, the usage bubble (and its little tail) gets a yellow ring. From 90% the ring turns red. At 100% it turns black with a silver edge. Change the yellow and red levels under "Warning levels", or switch the ring off with "Warn when nearly full" in the menu. When the 5-hour limit resets, it celebrates with three happy hops and hearts.
- **Idle habits:** it blinks, glances left and right, hops about every 30 seconds, and now and then breaks into a little dance with music notes.
- **Idle activities** (`pet/idle.py`): when it's done standing about, a 10% chance (`ACT_CHANCE`) of one of these. Claude starting work, or being picked up, interrupts them.
  Props go on the side towards the middle of the screen.
  - **Sweeping** (10–16 s): it holds a tall broom (red band, straw head) just outside its hand. The broom swings back and forth about its grip, and on each forward stroke it steps along the taskbar (about 45 px/s at 1x while pushing, never off the end of a window) and flicks dust and specks out ahead. At the end: "*sweeps it under the taskbar*".
  - **Painting** (13–19 s): an easel with a canvas beside it. It paints one of 9 little 12×12 pictures (flower, heart, sun in sunglasses, mushroom, the cat, a fish, a house, itself, a rainbow) block by block, one colour at a time, with a same-size brush in its dabbing hand and flecks of paint. Then it admires it with happy eyes and a heart, and names it ("I call it: 'Fun Guy'.").
  - **Fishing** (about 10–20 s): it cuts a hole in the taskbar right beside it (ice chips fly), sits down with a rod, and the bobber bobs with ripples. Two nibbles, a bite, and it reels up a fish (45%), a boot, a crab, a bug, a sock, or rarely a golden fish (5%). It holds it up on the line with a line to match, then drops it back in with a splash.
  - **Balloons** (2 or 3 of them): it blows one up in five big breaths (eyes squeezed shut), ties it, lets go, and it drifts up and outwards a little (clear of the usage bubble), string wiggling, then pops into bits ("bye, balloon."). No scared reaction.
  - **Paper plane**: it folds a sheet into a plane, holds it up, and throws it (usually towards the middle of the screen, sometimes the wrong way). The plane is its own little window (like the fetch ball) and flies like a glider: speed gives lift, gravity bends its path, drag slows it, and each throw gets its own trim speed, glide ratio and wobble, so paths differ (gentle glides, swoops, now and then a loop). It bonks off screen edges, lands on the taskbar, slides to a stop and stays 8 s. The mascot watches it and reacts to how far it went. One plane at a time.
  - The diary counts sweeps, paintings, things fished out, balloons popped and paper planes.
- **Coding jokes** (`pet/gags.py`): picked at random along with the activities above (each one as likely as any other), so they happen now and then when it stops walking. Each lasts 7 to 10 s, has its own props (bigger blocks than the small pictures, no dark edges), particles and lines, which it says as it goes rather than one line at the start. Props go on the side towards the middle of the screen. Anything over its head makes the usage bubble move up (`gag_room`). The diary counts them ("Coding jokes").
  - **Phone call:** a phone buzzes on the floor with little sound waves (`ring`), it picks it up and holds it to its head: "hello, API! long time no see.", then something like "you're number 429 in the queue. please try again later.", and it hangs up.
  - **Cookie:** it eats a chocolate chip cookie in four bites (crumbs, a `crunch` each): "I love cookies. I accept all of them." ... "mmm. third-party cookies. the forbidden kind."
  - **Rubber duck debugging:** a duck pops up beside it; it explains its code, waving its arms, until a lightbulb lights up over its head: "OH. never mind. thanks, duck!" The duck squeaks and gets a heart.
  - **Coffee:** a mug with steam rising, held by its handle (the handle points back at it); two sips (eyes shut): "coffee in, code out." ... "this is my Java."
  - **Bug hunt:** a shiny green beetle (`BEETLE`, legs in two frames) scuttles along the floor. It creeps after it with a butterfly net held out ready at its middle (a round hoop with mesh across it and a bag drooping below: `draw_hoop`), below its head so the usage bubble never hides it, staying within about 110 px. Two swings miss (a puff, and the bug hops off); the third slams the net down over it (a dome of mesh on the floor, the bug wriggling under it: `draw_dome`). It lifts the net with the bug in the bag ("it's not a bug, it's a feature!"), then lets it go: the bug buzzes off on little wings (`BEETLE_WINGS`) and the net goes away in a puff.
  - **Infinite loop:** it walks back and forth faster and faster with a little arrow spinning over its head ("while (true) { walk(); }"), then gets dizzy: "forgot the break statement."
  - **Stack overflow:** it stacks ten thin pancakes on a plate (thin enough that the full stack, butter and all, stays below the top of its head, clear of the usage bubble), the stack wobbles, gets butter and syrup, and topples: "stack overflow!" ... "marked as duplicate. rude."
  - **Off by one:** it counts sheep jumping a fence; the fourth jumps back; it loses count: "there are 2 hard things in coding: naming things, cache invalidation and off-by-one errors."
  - **Fortune cookie:** it cracks one open (the halves fall, crumbs), a slip unrolls: "'git push --force brings bad luck.'", then laughs nervously.
  - **Merge conflict:** two sticky notes, << and >>, shove at it from both sides while it looks from one to the other; one gets thrown away: "...accept chaos."
  - **Recursion:** it looks into an oval hand mirror, which shows it holding a smaller mirror, which shows it holding a smaller one... "it's mascots all the way down."
  - **Lost semicolon:** the tiny gold ";" (`SEMI_SMALL`) has been lying on the floor the whole time, glinting now and then. It searches with a detective's magnifying glass (brass rim lit on its top left, blue glass with a shine and a winking glint, a brass collar and a wooden handle: `draw_glass`), walking out one way and then back past where it started. When the glass passes over the semicolon, the lens shows it big (`SEMI_BIG`, without its gap rows so it fits the glass). It picks it up and holds it high (the usage bubble moves up for it) and a green tick pops up beside it (`CHECK`): "found it! now everything compiles. probably."
  - **404:** it digs with an upright shovel (`SHOVEL`: a D-grip, a wooden shaft, a steel socket and blade): six strokes of stab, lean, lift and toss, the blade going into a hole that grows (the hole's front lip is drawn over the blade), dirt arcing onto a pile beside it. The last stroke clinks on something; the shovel gets planted in the pile, a treasure chest (`CHEST`) rises out of the hole, its lid pops open with light shining out (`CHEST_OPEN`), and a page floats up just above it with 404 in red (`draw_page`; the bubble moves up for it): "404: file not found. classic." Then the page goes in a puff, the chest sinks back and the hole and pile fill in.
  - **Tiny keyboard:** it types away on a tiny keyboard (keys light up, bits of code fly up, `typing`), then undoes it all with a row of ctrl+z arrows: "great session. zero lines changed."
- **Waking up:** a big stretch, both arms up.
- **Limit used up (100%):** it carries on as normal (walking, hopping, activities) and now and then says a "hard day's work" line. The bubble gets its black ring.
- **Wizard mode:** when tokens are going up, it puts on a wizard hat and casts sparkles with a wand. The hat (`HAT`, `HAT_COLOURS` in `pet/art.py`) is lit on its left and shaded on its right, has a crescent moon, a big star and twinkles, a tip that bends over, a gold band with a buckle, and a two-tone brim. It's 23 blocks wide with everything but the tip centred, so it sits in the middle of the head. The apprentices and the teleport use the same hat. It notices Claude Code within about 3 seconds, by reading its logs. It notices claude.ai chat and other apps when the 5-hour % goes up, which is checked every 2 minutes.
- **Talking:** speech bubbles type themselves out above the usage bubble. It says:
  - an encouraging or silly line every 4–10 minutes ("Sometimes"), but only when you're at the computer
  - something when work starts, now and then while it's working, and when a long job finishes
  - bored comments after 30 minutes with no token usage at all (and sometimes it dances to pass the time)
  - a polite request for attention after 20 minutes without a hover, poke or drag
  - screams when thrown, parachute lines, and dizzy lines after a hard landing
  - special lines when a limit hits 100%
  - milestones at 50%, 75%, 90% and 100% of each limit
  - a cheer when the 5-hour limit resets
  - replies to some pokes, plus poke-count milestones (10, 50, 100, 500)
  - "wheee!" when you pick it up, a yawn before sleeping, and a hello when you come back
  - a warning if your login expires
- **Standing on windows:** when it falls past the top of a window (dropped, thrown, or walking off an edge), it lands there. It follows the window smoothly if you drag it (its window is checked every frame), and falls off when the window closes, minimizes or maximizes. At a window's edge it either turns around or walks off (50/50).
- **Personality** (Settings → Mascot → Movement; replaces the old "Walk around" and "Jump now and then" switches): Parkour! / Lively / Normal / Chill / Statue. Hovering an option shows a tooltip (the same card as the panel's tooltips, `ui.Tooltip`) explaining it; the texts are the choices under "Personality" in `tips.py`. Each is a row in `PROFILES`: how often it keeps walking, how long it stands about or walks, walking speed, how often it hops and jumps to windows, nap chance, what it does at a window's edge, how keen it is on trips (`climb`, `stack`, `high`), how often it turns round mid-walk (`flip`), how often a new walk heads for another monitor (`roam`), and how often it does idle things (`act`). Parkour is almost always moving: it keeps walking 90% of the time, stands about for under a second, jumps to a window about every 3 s, always climbs at a ledge, heads for other monitors and does few idle things. In a 3-minute simulation (version 7.17, two monitors, no windows) it was moving 89% / 67% / 41% / 17% of the time (Statue only moves while sweeping). Statue = no walking, hops or jumps (it still reacts and talks). Old settings with walking off become Statue.
- **Walking with weight:** it speeds up to walking speed over `WALK_EASE` (0.3 s) and slows to a stop the same way, so turning round is a quick slow-down and speed-up rather than an instant flip (`walk_v`, `walk_step()` in `movement.py`). Bumping into something stops it dead. Running to you and chasing the ball are still a sprint.
- **Coming up short:** a jump whose feet are still below a window's top when it reaches the window's side slaps into the side like a wall (`leap_wall`): a boing, a little bounce back and a tumble, dizzy stars, a line (`SLAP_LINES`), then it slides down beside the window with no parachute. Jumping straight up from in front of a window can't hit its side, so a failed one just lands back in front. The jump plan also slows down if it would otherwise reach the side of a higher window before its feet clear the top.
- **Leap of faith:** walking to the edge of a window, it may first look for another window that way to jump to (`edge_leap`), else take a leap of faith (`dive`) if the drop is at least `DIVE_MIN` (150 px): a little spring off the edge, it tips head first into a swan dive (no parachute), and lands in a haystack with straw flying. The haystack (`pet/hay.py`) looks like the ones in Assassin's Creed: a plump pile with two lumps close together, a taller one and a lower one (which side is taller changes each time, `hay_flip`), lit from the top left by how its outline slopes (rising faces the light, falling away is in shade; that counts most near the top, and the two lumps are blended smoothly for this so the dip between them is a soft crease, not a line), with a light checker where one shade meets the next, straw strokes all over, stray straws sticking out and swaying, and a soft dithered shadow. It pops up below as soon as the dive starts (with a little boing), on a stage window (`Stage`) since it's far below the mascot. It squashes and wobbles as the mascot lands in it, the mascot sinks in, then rises until its eyes peek over the lumps (`hay_lift`; its middle stays buried). The back half of the pile is drawn behind the mascot and the front half in front. It sits there for `HAY_TIME` (1.3 s), then pops out; the pile it leaves squashes and shrinks away with straw flying, and a few straws stay stuck on its head for 3 to 6 s (`straw_t`) before falling off. Otherwise it turns around (`turn`) or walks off.
- **Which stunt off the edge:** when it goes for a leap of faith (`dive` chance), `edge_stunt()` picks one by the weights in `EDGE_STUNTS`: leap of faith 0.25, water bucket, bungee, zipline, fireman's pole and web swing 0.15 each. They need the same `DIVE_MIN` drop (except a zipline to another monitor) and share `edge_drop()` and `spring_off()` in movement. One that can't be done from there (no room, say) just doesn't happen, and it turns round or walks off as usual. If it's facing a monitor next door whose taskbar is lower than the window it's on (by at least 120 px), and "Stay on one monitor" is off (`cross_target()`, using `neighbour()`), then half the time it takes a zipline or web swing over to that monitor instead.
- **Water bucket jump** (`pet/bucket.py`): a Minecraft "MLG" water bucket. It holds a full bucket in its lead hand (`BUCKET` in `art.py`, 12 by 11 small blocks: handle, rim, water, iron), falls upright looking down (no swan dive, no parachute, no air drag), and says a line (`BUCKET_LINES`). `POUR_AHEAD` (0.16 s) before it reaches the floor it worked out when it jumped, it turns the bucket upside down and the water pours out in a stream (`splash` sound): a source block appears where it's going to land and flowing water spreads out from it a step at a time, `FLOW` (5) steps each side, each lower than the last, like Minecraft. It lands in it with a splash of droplets: no bounce, no dizziness, and the bucket is empty now (dark inside), with a line (`WATER_LINES`). It stands in the water for `WATER_TIME` (1 s); a see-through strip of water is drawn over its legs (`water_depth()`, in `render.py`) so it stands in the water, not on it. Then it scoops it up the Minecraft way: the bucket dips, the source block vanishes at once with a `bloop`, the bucket is full again, and the flowing water drains from the middle out. It shows off the full bucket for a moment (happy), then puts it away with a little twinkle. The water is semi-see-through (`gray75` stipple) with a lighter top and glints drifting along it, on its own stage window behind the mascot. If it comes down before it got the bucket out (it landed somewhere it didn't expect), it's an ordinary landing plus dizziness and a line (`BUCKET_FAIL`). Picking it up, hiding it or a trip puts the bucket away and the water drains. Counted as "Water buckets" in the diary.
- **Bungee jump** (`pet/bungee.py`): a wooden plank slides out from the window's top corner, sticking out `REACH` (36 px) past the edge, clamped to the window, with a ring under its end. It wears a harness while it's on (drawn in `render.py`, rotating with it): black webbing with a slight sheen: a belt with a silver buckle (no shoulder straps), and a strap down to a silver ring low between its legs (`HARNESS_C`, `HARNESS_RING`). The cord (`CORD_C`: yellow, with a shine down the middle, slanted braid marks every few pixels, and a dark edge so it shows on any wallpaper) goes from the plank's ring to the harness ring (`harness_xy()`). At the harness end is the thick part: a black sleeve over the bundle of cords, always 12 small blocks long whatever the cord's stretch (measured along the cord), with a metal band where the cord goes in and a clip onto the ring. It stands there tying on for `TIE_T` (0.9 s, with a line from `BUNGEE_LINES`), then springs off (`whoosh`). The cord is slack (sagging) for the first part, then a spring that only pulls when stretched past its rest length: stiffness worked out when it jumps so the first bounce's lowest point just misses the floor, light damping, and a little air drag so it swings and settles. It falls head first (`turn()` tips it like a swan dive while the cord is slack, then lines its feet up the cord, near upside down, `bungee_lean()`), bounces about four times (`twang` at the bottom of the first stretch), swinging a little. After 3.5 to 5.5 s the cord is let out, with more damping, until it dangles upside down about 34 px above the floor; it waves for `HANG_T` (0.8 s), unclips (`clink`) with a little hop, flips the right way up in the air and lands on its feet (happy, a line from `BUNGEE_DONE`). The cord springs back up to the ring with a wiggle and the plank slides back in. About 11 s from start to finish. It never touches the floor while on the cord. Picking it up, hiding it or a trip lets the cord spring back. The plank and cord are on their own stage window; while it's on the cord they're drawn after it moves, so the cord keeps up. Counted as "Bungee jumps" in the diary.
- **Zipline** (`pet/stunts.py`): a post pops up on the window's corner and a cable shoots out to a post far off, low enough that it lets go just above the floor: on this screen (no further than 1.4 times the drop, 900 px, or the screen's edge), or on the monitor next door, about 220 px past the edge. The cable can't be steeper than about 55° (it would run right behind the mascot), so with no room for that it doesn't happen. It hops up and grabs the trolley's handlebar with both hands (the bar tilts with it, `raised_hand()`), and whizzes down (`zip`): speeding up with a bit of drag (and never slower than 90 px/s on a gentle cable), legs trailing behind (tilting clockwise going right, anticlockwise going left), braking into the far post, where its legs swing on forward. The cable sags under its weight into a V where the trolley is (`zip_point()`, most in the middle, up to 45 px), and hangs in a gentle curve otherwise. It lets go, drops onto the floor (or the other monitor's taskbar, which becomes its screen as it crosses the edge), and the cable reels in and the posts sink away (`ZIP_LINES`, `ZIP_DONE`).
- **Fireman's pole:** a brass pole slides down from the window's corner to the floor, held by a steel bracket with a brace and a plate on the window, a collar, a brass knob on top, and a red landing mat at the bottom (`POLE_C`). It hops across reaching out for it (one arm up), and only once it's on the pole does it hug it: the bit of pole in front of it is drawn over its body by `render.py` (`pole_strip()`, a round pole with a shine and a shady side), with its hands and feet wrapped round it (a dark crease under each, `GRIP_C`). It slides down (`slide`), spinning round it (its eyes go round), squeezes to slow down at the bottom, lands on the mat, lets go, and the pole slides back up (`POLE_LINES`, `POLE_DONE`).
- **Web swing:** it jumps off, and 0.28 s later shoots a web from its raised hand (`thwip`) to a spot up ahead (`web_aim()`: forward and up at a steep angle, moved up if the bottom of the swing would hit the floor). It swings down and forward on it (a rigid rope: back onto the circle each frame), tilted along the web, and lets go just past the bottom of the swing on the way up (or by the screen's edge). Staying on this screen, it's in the air for 0.2 s, then shoots a second web (`thwip`) from its hand, pointing down and out, at the ground about 90 px ahead (kept on this screen, so near the edge it pulls it back in; on the floor or a window below, `web_ground()`). It's yanked down that web, faster and faster up to 1200 px/s, feet first (`web_pull()`), and the second web's splat stays on the ground a moment. Going over to the next monitor instead, it flips and flies across, with the let-go speed set so it lands about 140 px past the edge. Either way it comes down in a superhero landing (squash, no bounce). (If it's somehow already on the ground without `land()` noticing, `stunt_tick()` does the landing.) The strand stays stuck up there, swaying, and fades (`WEB_LINES`, `WEB_DONE`).
- **How near the edge:** a stunt stays on its screen and no nearer the edge than `stunt_room()`: the bigger of `self.half` and 112 px (at 1x). `self.half` is how far the screen clamp (`clamp_x()`) keeps it from an edge, and it grows to fit the speech bubble, so 112 px allows for a long line. If a stunt took it nearer, the clamp would shove it back every frame while the stunt pulled it out again (version 7.29 fixed exactly that jitter). If the drop is too small for a first web swing that clears the floor, it skips straight to the web at the ground.
- **Their window stays one size:** each stunt's stage window is placed once (the web swing's when its first web sticks, and only made bigger if the second web lands outside it), never following the mascot. A see-through window that's resized every frame flashes its dark background at the new edge.
- These three are counted as "Ziplines", "Pole slides" and "Web swings" in the diary. Picking it up, hiding it or a trip packs everything away and frees it. Their props are on one stage window, drawn after it moves while it's on them.
- **Jumping between windows:** about every 25 seconds (with Jump, Walk and Stand on windows all on) it looks for a window top it could reach: up to ~520 px sideways, from a bit below it to ~420 px above it, not covered by another window. It crouches, says something brave, and jumps. Its legs really manage about 300 px up, so higher targets always fail; it also eyeballs the sideways push (85–120%, and 15% of the time it badly misjudges it). Misses just plop down (no parachute), with an excuse. Settings: `LEAP_EVERY`, `LEAP_POWER`, `LEAP_REACH`.
- **Windows are solid:** a window in front of the one it stands on can't cover it. When one slides over it or is brought to the front, the pet gets pushed out the side it's nearer to (a quick scoot, not a jump). Pushed past the edge of its own window, it falls off. Cornered against the screen edge or another window, it drops straight through to the taskbar. The screen edges are hard walls, even when a window is dragged past them. Maximized windows count as walls too. On the taskbar, windows whose bottom edge ends on or above the taskbar push it aside too (it checks the windows within ~400 px of it). A window that goes down behind the taskbar is behind its floor, so it stands in front of it and isn't pushed; boxed in on the taskbar (a maximized window, say) it just carries on, since there's nowhere lower to go.
- **Time of day:** a "good morning" the first time you're at the computer after 5 AM. After midnight, a gentle "it's late, maybe wrap up?" about every 40–60 minutes. Between 11 PM and 6 AM it naps three times as often and walks slower.
- **Tool errors:** when a Claude Code tool call fails, it looks worried (raised eyebrows) for 3 seconds and sometimes says "oops".
- **Old numbers:** if the last successful check is more than 10 minutes old and more than 3 checks' worth (15-minute checks while idle, so 45 minutes then), the bubble turns grey and says how old the numbers are, for example "15m old". So it only shows when checks have actually been missed, not because idle checks are slow.
- **Idle:** while idle (see Polling), everything about it is lavender (`IDLE_C` in `art.py`, a colour nothing else uses): the bubble adds "idle" after the numbers, the panel's "updated ... · next check in" line starts with "idle ·" and turns lavender, hovering it shows a tooltip explaining idle (`Details.tips` / `show_tip()`; a small rounded card in the panel's colours, bold title and grey text), and Settings → About & stats → Claude login has a lavender line under "Next check in" saying why checks are slower and that they speed up again as soon as Claude is used.
- **Login renewals:** it watches Claude Code's login file. When Claude Code renews your login after it expired, the pet checks again straight away.
- **Notifications** (if on): at 90% and 100% of a limit, when a nearly-used limit resets, and when your login expires.
- **Sounds** (if on): a pop when poked, a scream when thrown, a chime at milestones and resets.
- **Memory:** it remembers when each limit last moved, which milestones it has already announced, your poke count, and when it last said good morning, even after a restart.
- **Early pace warning** (if on): once per window, when the forecast says you'd hit 100% at least 30 minutes before the 5-hour reset (12 hours for the weekly one), it says when, plus a notification. Only from 50% (weekly: 40%) and not past 90%, where the milestones take over.
- **Quiet mode:** no talking and no sounds (the bubble and notifications carry on). From the menu for an hour, during quiet hours, or while Windows is in Do Not Disturb, focus or presentation mode (if Windows reports it; see "Not tested yet"). The Plan tab says when it's quiet.
- **Session wrap-ups:** when a Claude Code session has had nothing new for 8 minutes, it sums it up in a speech bubble ("session wrap-up: 34 min on Token Tracker, 58 messages, 2.1M tokens."). Sessions that finished while you were away come as one line when you're back. Only sessions that ended after the pet started, with at least 4 messages. The Sessions tab has the details.
- **First start:** a short tour in five speech bubbles: the bubble, hovering, poking and throwing, and the right-click menu. Settings → About & stats → Show the tour again replays it. People who already had a memory file don't get it.
- **Every other start:** a welcome back that fits the time of day (it counts as the morning's good morning), then, if Claude Code was used on this computer, an offer to carry on with the last session's project: "shall we continue working on Token Tracker today?" (within 3 hours: "it's still warm"; after 3 days: "it's been 5 days since..."). It waits up to 15 seconds for the logs, so it knows the project.
- **Eyes:** when your mouse pointer is within about 420 px, it looks at it: left, right, up or down.
- **Seasonal outfits** (if on): a ribbed jack-o'-lantern with a glowing face on its head from 25 to 31 October, a Santa hat with its tip flopped over to a bobble from 1 to 26 December, a glossy top hat with a gold band and confetti on 31 December and 1 January, a polka dot party hat with a pompom on its birthday (9 October), and two hearts on springs on a headband on 14 February. All of them (and the nightcap) are drawn like the wizard hat: a lit left side, a shady right side, highlights and no dark edge (`PUMPKIN`, `SANTA`, `TOPHAT`, `PARTY`, `LOVE`, `NIGHTCAP` and their colours in `pet/art.py`). Each comes with a line once that day. Fireworks burst above it from 23:55 on New Year's Eve until 1 AM. The wizard hat takes the outfit's place while it works.
- **Pajamas at bedtime** (if on, the default): from the chosen hour (`bedtime_at`, default 11 PM) until 6 AM (`BEDTIME_END`), it wears a blue and white striped nightcap with a bobble (about the wizard hat's size, with a lit edge and a shady side; `NIGHTCAP` in `pet/art.py`) and carries a candle in a brass holder, with flickering rays of light round the flame (`CANDLE`, `CANDLE_BASE`). Neither has the dark edge other little pictures get (like the wizard hat). Both follow the way it's heading (or last headed, `self.dir`): the candle is in its lead hand and the bobble flops out behind it (`OUTFITS["bedtime"]` heading left, the flipped `"bedtime_right"` heading right). Asleep, it puts the candle down on the floor on that side. The nightcap wins over a seasonal outfit; the wizard hat wins over both, and the candle goes away while it works, dances, does an idle activity, is in the hay, or has its lead arm up (e.g. waving with the right hand while heading right). When bedtime starts while it's running (and awake) it says a line (`BEDTIME_LINES`); not when the pet starts up at night.
- **Wizard jobs** (`pet/magic.py`, animated in `screenshots/wizard-jobs.gif`): while it's a wizard, the last Claude Code tool it saw (by name, within 8 seconds) picks a job. The hat stays on for all of them, it holds itself to suit (hands out, wand raised, both arms up...), looks at the prop, and every job has its own particles. Props float beside it, on the side towards the middle of the screen.
  - **Reading** (Read, Grep, Glob, LS, NotebookRead): a detailed spell tome floats beside it (leather cover, gold corners, a red capital, writing, a pulsing blue sigil, a ribbon). A page turns every 3 seconds, between two spreads, and little gold and blue runes float up off it.
  - **Writing** (Write, Edit, MultiEdit, NotebookEdit): a quill scribbles line after line on a floating scroll, flicking ink and gold flecks; it conducts with one raised arm.
  - **Commands** (Bash, PowerShell, BashOutput, KillShell, Monitor): green runes rain down around it in columns, brightest at the bottom like falling code, some behind it and some in front; both hands up in turn.
  - **The web** (WebFetch, WebSearch): a crystal ball in a little gold claw cradle floats beside it, bobbing and drifting (wingardium leviosa): glass shaded lighter at the top, a pink and cyan nebula swirling inside, twinkling stars, a shine and a reflection. Its wand is raised, with a stream of sparkles from the wand to the ball.
  - **Helper agents** (Task, Agent): a summoning circle glows on the floor beside it and a little one of itself (hat and all) rises up out of it, then waves.
  - **Planning** (TodoWrite, plan mode, task lists): four sticky notes circle round it, tilting, passing behind and in front.
  - **Asking you** (AskUserQuestion): a big chunky golden question mark floats beside it, with a 3D edge, a band of light sweeping across it, a dot that bounces on its own, a coin-flip spin every 3 seconds, and three tiny coloured question marks circling it. It says Claude has a question. This one lasts up to 2 minutes and keeps the hat on while Claude waits.
  - **Add-on tools** (any `mcp__` tool): a rune circle on the floor round its feet, two rings turning opposite ways with runes riding round, sparkles rising.
  - **Thinking** (`thinking` blocks in the log): an ornate hourglass floats beside it (gold caps, turned wooden posts with rings, glass with a shine): the sand funnels down out of the top bulb in a thin flickering stream and piles into a mound below, with a twinkle in the glass. When it runs out (4 s) the hourglass turns itself over (0.5 s) with a little burst of sparkles.
  - **Shortening the conversation** (`compact_boundary` lines): a floating scroll rolls itself up and unrolls again, pulling sparkles in.
  - Anything else: the wand and sparkles, as before.
- **Apprentices** (if on): while it's a wizard and more than one Claude Code session is busy (wrote something in the last 45 seconds), little apprentice wizards stand beside it, one per extra session, up to 3.
- **Pet diary** (Settings → About & stats): counts pokes, pick-ups, throws, little hops, jumps to windows (made and missed), leaps of faith, water buckets, bungee jumps, ziplines, pole slides, web swings, parachutes, wall splats, monitor hops, dances, naps, games of fetch, distance walked, time as a wizard, resets, 100%s of each limit, UFO abductions, cats and shiny days. "Past-midnight sessions" comes from the Claude Code logs (all time: sessions with anything between midnight and 5 AM).
- **Rare surprises** (if on, only while you're at the computer and it's not working or asleep):
  - about 1 start in 500, it's a shiny gold colour that day, with little twinkles.
  - about once every 12 hours you're there, a UFO flies in, beams it up, keeps it a couple of seconds and drops it back (dizzy). Picking it up mid-abduction rescues it.
  - about once every 6 hours, a grey cat walks along the taskbar. It stops to say hi to the mascot. Click it and it meows and runs off.
- **Auto-hiding taskbar:** it stands on the bottom edge of the screen, and rides up on the taskbar when it slides up (checked 10 times a second only while auto-hide is on).
- **Usage service changed:** if the usage answer stops looking like it used to (no 5-hour or weekly limit, or not even JSON), the bubble says "service changed", the panel explains, and `pet_errors.log` gets the names of what came back (never the values). It keeps trying.

Only one pet runs at a time. Starting it again while it's already running calls the running one over to your mouse, so **quit the old one first** (right-click → Quit) after updating the files.

## Fixing problems

- **The pet acts strangely or won't start:** delete `data/pet_settings.json` and start it again. All settings go back to their defaults.
- **The pet won't start at all:** to see the error message, open this folder in File Explorer, click the address bar, type `cmd`, press Enter, then type `py claude_pet.py` and press Enter. The error appears in that window.
- **Nothing happens when you start it:** a pet is probably already running. Starting it again calls it over to your mouse (a pet from before version 7.0 doesn't know how). It may be hidden because something is full-screen.
- **The bubble says "service changed":** Anthropic changed the undocumented usage service. Look in `pet_errors.log` for the names it sent back, and give them to Claude to update `pet/usage.py`.
- **It's silent and doesn't talk:** check the Plan tab for "Quiet mode", the menu for "Talk again", and Settings → Sound & talking → Quiet.
- **"Rate limited" / the bubble says "slow down":** the usage service answered "too many requests". This used to happen with the old 30-second and 1-minute refresh settings, and can still happen after restarting the pet several times in a row (each start checks straight away). Your last numbers stay on screen. It waits 3 minutes, then 6, 12 and so on (up to 30, or longer if the service asks), and goes back to normal after the next successful check. The wait is saved (`blocked_until` in the state file), so restarting the pet doesn't skip it, and "Check now" does nothing until it's over.
- **The bubble says "login expired":** open Claude Code once so it refreshes your login. The pet notices the renewed login file and checks again straight away.
- **Other words in the bubble:** each way a check can fail has its own message in `pet/usage.py` (the bubble and tray show a short word, the details panel and Settings → Usage the whole thing, with when it'll try again). Every message has two parts split by a blank line: what went wrong and why, shown in red, then what to do about it, shown in blue (`FIXC` in `details.py`, `FIX` in `settings_window.py`). When there's nothing to do (the cooldown, a server problem, the service changing), the blue part says so and that it should sort itself out. Refusals and redirects wait 30 minutes; the rest back off from 2 to 15 minutes.

  | Bubble | Cause | Message in `usage.py` |
  | --- | --- | --- |
  | login refused | 401 with a login that hadn't run out yet | `LOGIN_REFUSED` |
  | access denied | 403: probably not a Claude plan login | `ACCESS_DENIED` |
  | service moved | 404 or 410: the address is gone | `NOT_FOUND` |
  | rejected | another 4xx: the service changed what it accepts | `REJECTED` |
  | redirected | 3xx: never followed, so the token can't go elsewhere | `REDIRECTED` |
  | server error | 500 and other 5xx | `SERVER_ERROR` |
  | service down | 502, 503, 504 | `SERVICE_DOWN` |
  | overloaded | 529 | `OVERLOADED` |
  | no answer | no reply in 10 seconds | `NO_ANSWER` |
  | offline | api.anthropic.com couldn't be looked up | `OFFLINE` |
  | can't verify | the secure connection couldn't be checked (clock, antivirus, work network) | `INSECURE` |
  | blocked | connection refused or cut off | `BLOCKED` |
  | odd answer | a reply that isn't JSON (a Wi-Fi sign-in page, a proxy) | `UNREADABLE` |
  | service changed | JSON without the 5-hour or weekly limits | `SERVICE_CHANGED` |
  | check failed | anything else | `CHECK_FAILED` |
- **"Slow down" keeps coming back:** open `data/pet_usage.log` (see below). Look at `since_last`, `req10m` and `req1h` on the lines just before the first 429, and at `why`. A run of `why=start` lines means restarts, `why=manual` means the Check now button. It can't tell you the service's own reason (it doesn't give one), only what we'd been doing.
- **Something seems broken:** look in `data/pet_errors.log`, or send it to Claude. It never contains your login token.
- **A keyboard shortcut does nothing:** another app may already use Ctrl + Alt + P or D. `pet_errors.log` will say so. Settings → Shortcuts shows "Another app already uses these keys" under it; click it and pick different keys.
- **The bubble says "no login":** Claude Code isn't signed in on this computer. Run `claude` once and sign in.
- **It hides when it shouldn't, or doesn't hide during full screen:** turn off "Hide during full screen" (Settings → System), then tell Claude which app caused it.
- **"Start with Windows" stops working after a Python update:** turn it off and on again in Settings → System. (New shortcuts use the `pyw` launcher, which follows Python updates; only computers without the launcher point at one Python version.)
- **Two pets start with Windows:** an old version may have left its own startup shortcut. Press Windows + R, type `shell:startup` and press Enter, then delete `Claude Usage Widget` if it's there.

## Where the numbers come from

- `GET https://api.anthropic.com/api/oauth/usage` is an **undocumented** endpoint, so it can change or break without notice.
- Request headers:
  - `Authorization: Bearer <token>`
  - `Content-Type: application/json`
  - `User-Agent: usage-widget/0.1` (if that's ever refused, try `claude-code/2.1.204`)
  - `anthropic-beta: oauth-2025-04-20`
- The token comes from `~/.claude/.credentials.json`, at `claudeAiOauth.accessToken`. That file only exists because Claude Code is installed and signed in.
- **Token rule:** the token is never printed, logged or saved. It's only ever sent to `https://api.anthropic.com`.
- **Response:** `five_hour`, `seven_day`, `seven_day_sonnet` and so on, each shaped like `{utilization, resets_at}`. Unknown extra fields also appear (for example `iguana_necktie`). They're hidden unless they're a 5-hour or 7-day window (setting: `ONLY_KNOWN_LIMITS`).
- **What the numbers cover:** they're for the whole plan, so they include claude.ai chat, the desktop app and Claude Code together.
- **Testing rule (read this before running anything): never poll the real usage service in tests.** The service throttles hard and answers with a wait of up to an hour that nothing can shorten (see "Rate limits" below), and it's the same login Claude Code uses. Unless the task is working on the usage code itself, set the environment variable `PET_FAKE_USAGE` before starting or importing anything from `pet/`: `ok` (made-up numbers: 40% on 5-hour, 20% weekly), `offline` (no connection), or `429` (a slow-down with a one hour wait). In that mode `fetch_usage()` never reads the login or touches the network, the 60-second minimum gap between checks is skipped, and `pet_usage.log` isn't written. When a test does have to use the real service (usage code work only), make as few requests as possible, never loop, and say so in the change log. In PowerShell: `$env:PET_FAKE_USAGE = "ok"`.
- **Polling:** every 2 minutes by default (Settings → Usage → Refresh every, 2 to 5 min). After a 429 ("slow down") it waits 3 minutes, doubling each time it repeats (up to 30 minutes), or the service's `Retry-After` if that's longer (now 15, 30, then 60 minutes; see below). For 3 hours after a 429 (`SLOW_AFTER_LIMIT`, from `limited_at`, saved in the state file) it checks half as often (every 4 minutes on the 2-minute setting). The wait is saved in the state file (`blocked_until`), so a restart or "Check now" can't skip it. When nothing has used tokens for 10 minutes (`IDLE_AFTER_MIN`, judged from `last_usage`), it checks every 15 minutes (`IDLE_POLL_SECONDS`) instead, and goes back to the normal pace as soon as tokens move again. Chat on claude.ai that doesn't show in Claude Code's logs can take up to 15 minutes to appear while idle. **Expired login:** the token's `expiresAt` (milliseconds) is checked first, and while it has passed no request is sent at all (Claude Code renews it only when it runs; asking with an old token gets 401s, and three or so of those in a row get a 429 with a 60-minute wait). A change to the credentials file triggers a check straight away. After a real 401 it waits `REFUSED_RETRY_SECONDS` (30 min) unless the file changes sooner. **Other failures:** any other refusal (a 4xx such as 403) waits `REFUSED_RETRY_SECONDS` too (a changed credentials file still wakes it). Server errors (5xx), timeouts, no connection and answers it can't read back off: the poll gap, then double, up to `ERROR_RETRY_MAX` (15 min), back to normal after the next good check. Before 7.38 these were retried at the full pace forever, which is how a run of 401s turned into a 429.

**Rate limits (what's known, from other people's reports as of 2026-10; none of it is documented by Anthropic):**
- `/api/oauth/usage` is throttled much harder than the model itself, and the throttle seems to be per login token. People polling every 30-60 seconds hit 429 after about 5 requests. Some got 429 even at 10-minute gaps. `Retry-After` is sometimes missing or `0`, and sometimes 3037 to 3600 seconds (we've seen about 3538).
- **Claude Code uses the same endpoint with the same login** (found in `claude.exe` 2.1.x: `/api/oauth/usage`, plus `?at_wall=1&skip_spend=1` and `?cedar_ember=1&skip_spend=1`). So the throttle's budget is shared, and a 429 can come at a pace that worked for hours, when Claude Code happens to ask too. Seen 2026-10-16: two 429s (`retry-after=0`, no `request-id`) at a steady 2-minute pace, about 6 per 10 minutes, one after 70 good checks in a row. How often Claude Code asks isn't known.
- Retrying inside the wait seems to keep the throttle alive, so after a 429 the pet waits at least 15 minutes (doubling to 60) or the service's `Retry-After`, whichever is longer, and never sooner after a restart (`blocked_until` is saved).
- Every request is spaced at least `MIN_FETCH_GAP` (60 s) from the last, including across restarts (`last_fetch` is saved), and the gap has a little random jitter. When nothing has used tokens for `IDLE_AFTER_MIN` minutes it checks only every `IDLE_POLL_SECONDS` (15 min).
- Ideas that were looked at and **not** used: refreshing the login token to get a fresh throttle (refresh tokens are single use, so it can log Claude Code out); a tiny `POST /v1/messages` call that reads the `anthropic-ratelimit-unified-5h-*` headers (costs a real, if tiny, message against your plan, and is another thing that can be throttled); reading claude.ai with a browser session cookie (a different login that must never be handled here).
- **Tried on 2026-10-11, not built: the best option on paper, but it didn't run in the desktop app.** A throwaway status line was added to the user's settings (and removed again afterwards). Run by hand it worked, but after a new Claude desktop app Code tab session got a message it never ran, so the bridge probably only works in the terminal version of Claude Code. Not tried in a terminal. The idea: Claude Code's `statusLine` command is handed `rate_limits.five_hour.used_percentage`, `rate_limits.five_hour.resets_at` and the same two for `seven_day` on every update (Claude Code 2.1.80 or later, subscribers only, only after its first reply in a session; the values are for the whole plan, so they include claude.ai chat as of that moment). A tiny script set as the status line could write them to a file in `data/` for the pet to read with no request at all, and the pet would then only call the service when that file is stale. It needs a change to the user's `~/.claude/settings.json`, which also replaces any status line they already have, so it has to be asked about first.

**Claude Code token counts** come from its local logs:
- Files: `~/.claude/projects/**/*.jsonl`, one JSON object per line.
- Assistant lines have `message.usage` (`input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`), plus `message.model`, `message.id`, `requestId`, `timestamp` (UTC), `sessionId` and `uuid`.
- **Each answer is logged several times** (once per content block, with the same usage repeated).
- **Resumed or forked sessions** start their new log with a copy of the old conversation (same line `uuid`s). `seen_lines` remembers which log each line was first in; a line seen again in a *different* log is a copy (`line_copies`, and its answer goes in `copies`), while the same log read again is ignored.
- **"Count tokens like the Claude app" (default):** adds up every copy, like the Claude desktop app, both the repeated content blocks and the lines copied into other logs (so "Messages" and "Total tokens" match the app), and "Peak hour" is the hour most sessions *start* in (see "Peak hour, app way" below).
- **Switched off (real count):** each `(message.id, requestId)` pair is counted once, about 3× lower, and "Peak hour" is the hour with the most messages.
- "Messages" counts every user and assistant line: each `uuid` once in the real count, every copy in the app count.
- **Peak hour, app way** (from Claude Code GitHub issues #65775 and #83678, not official docs): one count per log file, at the local hour of its *first* user or assistant line in file order (not the earliest time in it), and always all-time, whatever range is picked. On a tie the pet keeps the hour that got to the top first (that matched the app on 2026-10-11, with 12 PM, 5 PM and 10 PM tied). The app reads this from its own cache, which can lag behind, so it may still differ for a while after new sessions.
- "Total tokens" is input + output + cache write + cache read.
- Only numbers are kept from the logs (times, session ids, model names, token counts, the project folder's path and each session's name in the Claude app), never message text. Live, it also notes which tool Claude just used, by name only (`message.content[].name` of a `tool_use`), never what the tool was given.
- **The cache:** after the first full read, everything kept above is saved to `pet_cc_cache.json.gz` with how far into each log it got, and saved again every 5 minutes when something changed. On start the pet loads it and only reads what's new. If any log it knew got shorter or disappeared, the cache is thrown away and every log is read again, so deleted logs drop out of the stats as before. Logs are read 4 MB at a time, and a single line bigger than that is skipped.
- Claude.ai chat has no local token log, so there are no token numbers for chat. Only the plan % covers it.
- **Cost estimate:** what the same tokens would cost on the pay-as-you-go API (your plan covers them, so it's only for comparison). Always counted once per answer, whichever counting mode is on. Prices are in `PRICES` near the top of `pet/cclog.py` (dollars per million: input, output, cache read). Cache writes cost 1.25× input for the 5-minute cache and 2× for the 1-hour cache, using the 1-hour amount the logs record. Models with no price are left out, and the panel says so.
- **Projects:** each answer's `cwd` (the folder Claude Code was working in), kept as the whole path (Git Bash's `/c/Users/...` spelling becomes `C:\Users\...`). Names are worked out each time the stats are built (`named` in `pet/cclog.py`):
  - A folder inside a git repo counts as the repo's top folder. A folder that no longer exists counts as the nearest folder above it that sessions also worked in (so an old `Token Tracker\pet` joins `Token Tracker`).
  - **Renamed or moved folders:** when a log's lines go from one folder to another (not into or out of a subfolder), that's saved as a move. A resumed or forked session starts its log with copies of the old lines, so continuing a session after renaming its folder records old → new. A folder that no longer exists follows its moves to where work carried on. Moves are kept in the log cache. Known limit: a session that `cd`'d into another project, in a folder that was later deleted, also counts as a move.
  - **The name:** the Claude desktop app's name for that folder if it has one (`%APPDATA%\Claude\ccd-session-presets.json`, read fresh each time, so renaming a project in the app shows up), else the folder's name.
  - **Folderless app chats:** the app runs these in a made-up `scratch-YYYY-MM-DD-xxxxxx` folder. One that moved into a real folder counts there; otherwise it shows the chat's name (the log's last `custom-title` line, `customTitle`), or "Untitled chat".
  - The Projects view shows the top 5 by tokens with bars and session counts, then up to 10 more as one line each in a second card.
- **Chat context** (the Plan tab's "Context window" card and "ctx" in the bubble): the newest assistant answer by time that isn't a subagent's (`isSidechain` false). Its input + cache write + cache read is everything the model was sent, so it's how full that chat's context was. It's saved in the log cache as `context`. The logs don't say which context window a chat has (no `[1m]` anywhere), so the size comes from `CONTEXT_WINDOWS` in `pet/config.py` by model (Opus 5 and Sonnet 5 are 1M; anything else 200k), and anything past 200k is taken as 1M. It updates after each reply, not while Claude is still writing. "Latest" means the chat that replied last, so with two chats going it follows whichever answered most recently. In the bubble (Bubble shows: Limits + context) it sits right after the limits (so "idle", "old" and "!" stay at the end), and it's left out once that chat hasn't replied for `CONTEXT_FRESH_MIN` (60) minutes.
  - Not used: running `/context` writes its whole table into the log as numbers (a `system` line, `subtype: "local_command"`, with `contextUsage`: `total_tokens`, `raw_max_tokens`, and `categories` of `name`/`tokens`/`kind`). A Context tab showing that split like the Claude app was tried in 7.46 and dropped for the simple card. It only exists for chats where `/context` was run.
- **Tool errors:** user lines whose `message.content` has a `tool_result` with `is_error: true`.

## How it's built (to rebuild from scratch)

**Rules:**
- Python standard library only (`tkinter`, `urllib`, `ctypes`). No pip installs.
- Windows only.
- Casual lowercase code comments, no docstrings.

**The window:**
- Borderless and always on top, with no taskbar button.
- The whole window is filled with one "key" colour, `#010203`. `-transparentcolor` makes that colour see-through, and clicks go through it to whatever is behind.
- The mascot and the little pictures (hearts, z's, sparks) are drawn as solid rectangles, not text, so their edges stay sharp. The small pictures get a 1-block dark shadow so they show on any wallpaper.
- Text only ever sits on the solid dark bubble.

**Screens:**
- `EnumDisplayMonitors` and `GetMonitorInfoW` list every monitor's full area and its "work area" (the area without the taskbar). This is checked again every 5 seconds.
- The pet's position is its centre `x` and its feet `y`, in real screen pixels. The floor is the bottom of the work area of the screen it's on.
- The process uses `SetProcessDpiAwareness(2)` (per-monitor) so positions are correct on every screen.
- **Gotcha:** Tk window positions must be written `+x+y`, even when x is negative, for example `"123x87+-1022+945"`. Writing `-1022` means "1022 pixels from the right edge" and sends a window on a monitor left of the main one to the wrong place.
- Hidden windows (the pet during full screen, the closed panel) are parked at (-32000, -32000) instead of using withdraw/deiconify, which would steal keyboard focus.

**Full-screen detection (twice a second):**
- `EnumWindows` goes through windows front to back.
- It skips:
  - invisible or minimized windows
  - the pet's own windows
  - click-through overlays (`WS_EX_TRANSPARENT`) and tool windows (`WS_EX_TOOLWINDOW`)
  - cloaked windows (`DwmGetWindowAttribute` 14)
  - the desktop and taskbar classes
- For each screen, the first window that touches it decides:
  - **Full screen:** the window covers the whole monitor and isn't a normal maximized window (a window counts as normal-maximized when `IsZoomed` and it has a title bar).
  - **Not full screen:** the window covers at least 85% of the screen.

**Movement:**
- Walk speed is 28 px/s.
- A hop is 34 px high, about once every 30 seconds. Gravity is 1150 px/s². All of these are multiplied by the size.
- The air curve uses the exact formula (`y += vy·dt + ½·g·dt²`), so the height is right at any frame rate.
- Every jump starts with a 0.08 s crouch. A hard landing gives a 0.07 s squish. Holding the mouse button down squishes it too.
- Frame rate: a steady 60 fps while moving (`FPS`). Each frame is aimed at the next 1/60 s mark, and while moving the pet asks Windows for a 1 ms timer (`timeBeginPeriod(1)`), handing it back when it stops. Windows' normal 15.6 ms clock made some frames take 31 ms, and that was the jitter in throws. Otherwise: 33 fps while waving or showing hearts or z's, 12 fps while standing, and 2 fps while hidden. The canvas is only redrawn when something visible changes. Walking just moves the window.

**Monitor edges:**
- A neighbour is a screen whose edge touches this one and overlaps it vertically. It doesn't count if "Stay on one monitor" is on, or if that screen is showing something full-screen.
- The pet crosses once its centre passes the edge. A lower floor means it falls. A higher one means it jumps by (height + 12 px), up to 400 px at 1x (`MAX_STEP_UP`). Anything higher: when it walks to the point where it would normally stop (its `half` in from the edge), it takes a trip there (the personality's `climb` chance); otherwise it carries on to the edge and turns around. No neighbour at all means it turns around.

**Trips (`pet/travel.py`):**
- Three kinds of trip. **Side:** a neighbour (as above) whose taskbar is more than `MAX_STEP_UP` higher; it checks this in `move_x` while walking (not while running to you, chasing the ball, sliding after a throw, or up on a window), with the personality's `climb` chance. **Stacked:** `stacked()` (in `screens.py`) lists screens whose top touches this one's bottom or the other way round, sharing more than 200 px of width, with the same "Stay on one monitor" and full-screen rules as neighbours; walking on the taskbar it thinks about going to one on average every `stack` seconds of walking (personality). **Window:** `try_leap()` also collects windows it can see (not covered at that spot, on this screen, top inside the screen, within 1.5× `LEAP_REACH`) that are too high to jump to (more than 1.4× `LEAP_POWER` up). With the personality's `high` chance (30% of that when there's also a window it could jump to) it takes a trip onto one of them instead. That works from the taskbar or from another window.
- Nothing is fixed to one layout: `start_trip(to, how=None, win=None, tx=None)` works everything out from the screens (`self.screens`, refreshed every 5 s) and windows as they are when it sets off: the target spot (side: `half` in past the edge; stacked: near its x, inside the shared part; window: near its x, inside the window), whether there's room, and which ways fit. A change of monitors mid-trip stops the trip (`apply_screens`), and a window trip stops if its window moves, closes or goes away (checked every frame; already standing on it, it just rides along as usual).
- Which ways fit: portal and teleport always. Going down to a stacked screen: also wings, jetpack, UFO, and the trapdoor when it's standing over the shared part. Going up (for a side trip only if there's room on this screen to get level with the ledge): also wings, jetpack, balloons, UFO, cannon, and the climbs (rope, ladder, beanstalk, and boxes for rises under 800 px) when there's a spot to climb from on the floor it's on (beside the screen edge, or under the target). A side trip to a lower screen isn't a trip: it just walks off as before. The climbs first walk to their spot (with the same speed-up and slow-down as walking).
- While on a trip, `self.trip` holds it (a dict: `how`, `stage`, times, start, target, climb spot, `fade`, `clip` and the stage's particles), `state` is `"trip"`, and `physics()` hands every frame to `trip_tick()`, which moves the mascot itself (no normal gravity, no window landings), so window jumps, leaps of faith and the rest aren't touched. `self.si` follows whichever screen it's over, and `clamp_x` leaves it alone.
- Speed curves: flying (wings, jetpack, balloons, UFO) follows a path of straight bits (up, across, down) at a speed set by how far it is from the nearest corner or end, `sqrt(2 × acceleration × distance)`, capped at a top speed (`FLIGHT`): it speeds up from a standstill, slows into each corner and comes to a gentle stop. Climbing goes in steps that each speed up and slow down (rope pulls, ladder steps), the beanstalk grows on a smooth curve, the ladder sections slide out and slow into place, the boxes and cannon are real jumps under gravity.
- The stage: things away from the mascot (rope, hook, ladder, beanstalk, boxes, cannon, portals, trapdoor) and all the trip's particles (dust, smoke, sparks, leaves, flames, feathers) are drawn on one see-through, click-through window over the whole trip (`Stage` in `sprites.py`, made once and reused), in screen pixels, so smoke trails stay where they were made. It's placed with `move_window` (Tk sometimes held the move back, and props were drawn 110 px out), and hidden by emptying it and shrinking it to 1×1 where it is (parking it off screen didn't come back reliably). The mascot's window is lifted in front of it when it appears. Wings, jetpack, balloons, the whirling hook, the portal gun, the wizard hat and the UFO are drawn in the mascot's own window (`draw_trip()`; wings, jetpack and the UFO's beam behind the body). Nothing has the dark edge the older little pictures have.
- Sinking through a portal or the trapdoor: `trip["clip"]` is the floor's screen y, and the body's blocks are cut off below it (`emit` in `render.py`). Teleporting: `trip["fade"]` 1 to 3 draws the body with Tk's `gray75` / `gray50` / `gray25` stipples (`FADES`), and 4 hides it (also inside the cannon and the UFO). Its outfit is hidden meanwhile, and the usage bubble steps aside except while flying with wings, jetpack or balloons, or using portals.
- Timings (seconds): rope: whirl 1.3, throw at least 0.35, tug 0.7, climb at 80 px/s or faster (at most 8 s) in pulls of 0.42 (`PULL`), haul over 0.6, reel in 0.75. Ladder: out 0.5, unfold 0.8 to 2.4, steps of two rungs at most 0.32 each (at most 6.5 s), fold 0.6. Beanstalk: plant 1.0, grow 1.4 to 4.5, shrink 1.0. Boxes: up to 14 boxes (at least 34 px tall each), a pause of 0.14 between hops. Wings: sprout 0.6, top speed 170 px/s (or faster, so at most about 9 s). Jetpack: 0.8 of coughs, top speed 330 px/s. Balloons: puff up 1.2, top speed 85 px/s, let go 45 px above the floor. UFO: arrive 1.4, beam up 1.6, top speed 260 px/s, beam down 1.3, leave 1.4. Cannon: aim 1.0, hop in 0.5, fuse 1.1, the shot peaks 90 px (plus a bit for distance) above the higher end. Portals: blue shot at 0.5, orange at 1.6, each opens in 0.3, out of the orange one fast enough to rise 120 px. Teleport: hat 0.5, sparkles 1.1, fade out 0.65, fade in 0.7. Trapdoor: two stomps in 0.9, opens for 0.35, then it falls.
- It stops a trip cleanly (`end_trip()`: stage emptied, back to idle, and if it was up in the air it falls straight to the taskbar) when it's picked up, hidden (full screen or Ctrl + Alt + P), called over, sent to fetch, when the animations are switched off, or when the monitors change.
- Sounds: `clink` (the hook biting, the trapdoor latch), `flap` (wings), `zap` (portal gun), `boom` (cannon), `jet` (jetpack), `thud` (each box); also `pop`, `whoosh` (the UFO) and `spell` (teleport). Lines: `ROPE_*`, `LADDER_*`, `BEAN_*`, `BOX_*`, `WING_*`, `JET_*`, `BALLOON_RIDE` / `_DROP`, `UFO_RIDE` / `_END`, `CANNON_*`, `PORTAL_*`, `TELE_*`, `HATCH_LINES`. Pictures and colours in `art.py`: `HOOK` (prongs up, the ring for the rope at the bottom), `ROPE_C`, `WINGS`, `GUN`, `PORTAL_C`, `HATCH_C`, `LADDER_C`, `STALK_C`, `SOIL_C`, `BOX_C`, `CANNON_C`, `FLASH_C`, `JET_C`. The diary counts `trips` ("Monitor hops").

**The mascot:**
- It copies the Claude Code welcome-screen shape:

  ```
   ▐▛███▜▌
  ▝▜█████▛▘
    ▘▘ ▝▝
  ```

- Each terminal character is 2×2 blocks, so the mascot is 18 blocks wide and 5 blocks tall.
- One block is 4×8 pixels at 1x.

  ```
  row 0  ...############...   (asleep: breathing narrows this row every 1.4 s)
  row 1  ...############...   eyes: dark blocks at columns 5 and 12
  row 2  ..##############..   arms: blocks at (1,2) and (16,2)
  row 3  ...############...
  row 4  legs   standing: 4, 6, 11, 13
                walking:  5, 7, 10, 12  (alternates with standing every 0.18 s)
                in air:   3, 5, 12, 14  (held: wiggles between air and walking)
  ```

**Faces and poses:**

| Pose | How it's drawn |
| --- | --- |
| Blink or asleep | Each eye becomes a thin line in the lower half. |
| Happy | The eye line moves to the top, plus pink cheeks at (4,2) and (13,2). |
| Glancing or walking | The eyes shift one column. |
| Waving | The right arm moves to (15,1)+(16,1) or (15,1)+(16,0), swapping every 0.18 s. |
| Lying down (asleep) | The body sinks one block and the legs are hidden. |
| Squished | The body sinks half a block. |

**Rounded boxes:**
- Three rectangles plus four corner images, all on whole pixels.
- Each corner is made once and reused. It's sampled 4×4 per pixel.
- In the details panel the edge is blended into the panel colour, which makes it smooth.
- On the see-through window, each pixel is either fully in or fully out, because blending into the key colour would leave a coloured fringe.

**Little pictures** (each block is 2 px at 1x):

| Picture | Pattern | Behaviour |
| --- | --- | --- |
| Heart | `.##.##. / ####### / ####### / .#####. / ..###.. / ...#...` | Pops out above the bubble. |
| Z | `#### / ..#. / .#.. / ####` | Two sizes. Drifts up behind the bubble. |
| Spark | `.#. / ### / .#.` | Shoots from the wand tip in gold, cyan, pink or white, and drifts behind the bubbles. |
| Wizard hat | 24×11 blocks: a purple cone leaning right, a star of `*` in the middle, a gold band and a wide brim (see `HAT` in the code) | Sits on the head while working. |

**Wizard pose:**
- The right arm swaps between (15,1)+(16,1) and (15,1)+(16,0) every 0.35 s.
- A 5-block brown wand goes diagonally up and right from the hand, with a 2×2 gold tip.
- The eyes look toward the wand.
- The usage bubble moves up to make room for the hat.

**Colours:**

| What | Colour |
| --- | --- |
| Mascot | `#d77757` |
| Eyes and shadows | `#2b1a14` |
| Cheeks | `#f4a08f` |
| Heart | `#ff6f8a` |
| Z's | `#f2efe8` |
| Warning ring | `#f2c14e` (yellow), `#e5534b` (red) |
| Bubble | `#1f1e1d` |
| Bubble text | `#f2efe8` |
| Speech bubble | `#f2efe8`, with text `#2b1a14` |
| Hat, band, star | `#6c4ab6`, `#f2c14e`, `#ffe08a` |
| Wand | `#8b5a2b` |
| Activity grid | `#2c2c2e` for an empty day, then `#173c6e`, `#1f57a6`, `#2b74e0`, `#5aa2ff` from quiet to busy |
| Usage dots | green `#4caf7d` under 60%, amber `#d9a441` under 85%, red `#e5534b` from 85% |

**Window layout (bottom to top):**
1. The mascot.
2. Room for the hat (only while working).
3. A 2 px gap and the bubble's tail.
4. The usage bubble.
5. The speech bubble (only while talking).
6. 40 px of empty space at 1x for hearts.

There's also 30 px of side space for z's and sparks.

**Usage bubble, "bars" style:**
- One row per limit: a small label (`5h`, `wk`), then a 56×5 px bar in the usage colour on a `#3a3a3c` track.
- A red dot in the corner when the last check failed.
- With no data yet, it falls back to the numbers style.

**Talking:**
- Speech is wrapped to 190 px at 1x and types out at 30 letters a second. It stays up for 2.6 s + typing time + 0.03 s per letter.
- `say()` has a 20 s cooldown for chit-chat (8 s on "a lot"). Lines about something that just happened skip the cooldown.
- Small talk comes every 45–120 s (`CHAT_GAP`, divided by the chatter rate), picked by `small_talk()` from what it's doing: walking (3 times in 4 while it walks), dancing, standing on a window, or quotes, curious questions and fourth-wall lines (`FOURTH_WALL`). While napping it sometimes talks in its sleep.
- `pick()` avoids the last 60 lines it said.
- No talking when chatter is off or the pet is hidden.
- Random lines and quiet-time comments only happen when someone has touched the mouse or keyboard in the last minute, and not while it's working, asleep or showing the panel.
- "Chatter" changes how often: sometimes = ×1, a lot = ×2.5, non-stop = ×5.
- All the lines are lists in `pet/lines.py` (`QUOTES`, `CURIOUS_LINES`, `WALK_LINES`, `HIGH_LINES`, `DANCE_LINES`, `SLEEP_LINES`, `FALL_LINES`, `LEAP_TRY`, `LEAP_OK`, `LEAP_FAIL`, `SQUISH_LINES`, `WORK_START`, `WORKING`, `WORK_DONE`, `IDLE_LINES`, `POKE_LINES`, `POKE_COUNT`, `DRAG_LINES`, `WAKE_LINES`, `RESET_LINES`, `MILESTONES` and more).

**Working (wizard) detection:**
- A background thread reads only the new bytes of each log file every 3 s.
- New output tokens mean it keeps working for 20 more seconds.
- A rise in the 5-hour % (after the first check of each run) means it keeps working for 130 more seconds, which covers the next 2-minute check.
- No napping while working. If it was asleep, it wakes up for work.
- The "starting work" line (`WORK_START`) is only said when no other line is up, so it never cuts off a milestone, the pace warning or the reset line that came with the same usage check.

**Milestones:** announced once per limit window, with the window identified by `resets_at` (±10 minutes). On the very first run, levels already passed are recorded quietly instead of announced.

**Plan tab chart:**
- Plots `history` points that fall inside the current window (window start = `resets_at` minus 5 hours or 7 days) plus the current %, against a dashed pace line from 0% at the start to 100% at the reset.
- Forecast: projected % at reset = used % ÷ elapsed % × 100. If that's 100 or more, the run-out time is start + elapsed × 100 ÷ used %.
- **Before the pet's first check in the window** there's no real %, so that stretch is estimated and drawn dotted ("dotted = estimate"). Claude Code's token use from the window start up to the first real point becomes a running total, weighted roughly by cost (input ×1, output ×5, cache write ×1.25, cache read ×0.1). It's then scaled so it ends exactly at the first real %. With no Claude Code activity in that stretch, it's a straight dotted line. Claude.ai chat use isn't in the logs, so the estimate's shape only reflects Claude Code.
- With no data and no estimate it shows "the line fills in as I check your usage". The real history only grows while the pet is running.

**Memory file (`pet_state.json`):**
- Holds `seen` (per limit: %, when it last changed, `resets_at`), `last_5h`, `pokes`, `milestones`, `last_usage` and `history`.
- Also `greeted` (the date of the last "good morning"), `pace_warned` (per limit: the window it already warned about), `recapped` (the last 50 sessions it wrapped up), `log` and `log_since` (the diary's counts and when it started), `hush_until` (quiet from the menu until then), `toured` (the tour is done; true for anyone who had a memory file before) and `season_said` (the date of the last seasonal line).
- `history` is `[time, 5-hour %, weekly %]` from each successful check: every check for the last 6 hours, then one per 10 minutes, kept for 8 days.
- Saved every 60 s and when you quit.
- Bad values are ignored.

**Sleep:**
- Away for `SLEEP_AFTER_MIN` (5) minutes, measured with `GetLastInputInfo`. It wakes when there's any input again.
- Random naps: a 6% chance whenever it stops walking.

**Celebration:** happens when the 5-hour % drops by 15 points or more from a value of at least 15.

**Hover:**
- Checked 10 times a second by comparing the mouse position (`winfo_pointerxy`) with the mascot and bubble rectangles. Enter/Leave events aren't used because they're unreliable on see-through windows.
- The panel opens after 0.3 s of hovering. It closes 0.35 s after the mouse leaves the mascot, bubble and panel, unless it's pinned.

**Details panel:**
- 340 base units wide, with two tabs, drawn in the settings window's palette (`BG #262624`, cards `#30302e`, `segmented()` controls, `card()`s sent to the back after their contents). It opens just above the bubble. If there isn't room (the mascot is high up on a window), it opens below the mascot, and if there's no room there either, beside it. It never covers the mascot or its bubble.
- It stays in front of other always-on-top windows: when it opens and every second while it's open, `to_front()` (in `ui.py`) puts it back at the front of the topmost windows with `SetWindowPos(HWND_TOPMOST)`, without taking focus. Its tooltip and the right-click menu are put in front of it after. `-topmost` alone wasn't enough: an always-on-top window opened after the pet started went in front of it.
- Its height is the tallest of Plan and the four Claude Code views (each is drawn once to measure it), so the controls stay put. Shorter ones leave space at the bottom.
- The **Plan** tab is the old widget's panel: bars, a pace tick, reset times and pace messages, plus "Claude Code today".
- The **Claude Code** tab has "Overview", "Models", "Projects" and "Sessions" views, and "7 days", "30 days" and "All time" ranges (not for Sessions). The selected tab, view and range are remembered.
- The activity grid is 26 weeks × 7 days with Sunday at the top. Each day's colour level is 1 + min(3, int(4 × day ÷ busiest day)).
- The book comparison picks the biggest book from a list that the total is at least twice the size of (book sizes are rough token counts).
- It fades in and out over 0.18 s with an ease-out curve, sliding up 10 px as it appears.
- Windows 11 gives it rounded corners (`DwmSetWindowAttribute` 33 = round).
- The mascot stops walking while the panel is open.
- Pace messages:
  - "ahead of pace" when used ≥ elapsed + 10.
  - "way under pace" when elapsed ≥ 20 and used ≤ half of elapsed.
  - "no usage lately" when the number hasn't changed for 45 minutes (5-hour) or 12 hours (weekly).
  - Nothing during the first 10% of a window.

**Dragging and throwing:**
- On press it remembers where on the body you grabbed (`grab_local`). While held, it tilts so its middle hangs straight below that spot (`hang_angle`), plus a swing from how fast you move sideways. A spring pulls the tilt toward that target.
- Tilted, every block is drawn as a turned square (polygon) around the turning point. The usage bubble steps aside, and speech sits just above the body.
- **The mascot's window is one fixed size in every state** (worked out from the size setting only, with room for the parachute, bubbles, 4 lines of speech and a fully tilted body). It's always placed by the body: window x = body centre − `center_x`, window y = feet − `feet_win`. Resizing or shifting the window when switching states (tilted, standing, parachute) made Windows flash a dark box or the mascot flicker for a frame, because moving a window and redrawing it don't happen at the same instant. Tilting turns the body around its middle.
- The window reaches about 20 px below its feet into the taskbar area. That part is see-through and click-through, so it doesn't get in the way.
- On release, the speed comes from the mouse movement over the last 0.12 s. It's heavy: mouse speeds under 250 px/s (`THROW_MIN`) just drop it, and faster ones keep 38% (`THROW_KEEP`) of the mouse speed, up to 1500 px/s (`THROW_MAX`). Air drag is 150% per second (`THROW_DRAG`) and ground friction is 1600 px/s² (`GROUND_FRICTION`). Measured: a quick 70 px flick travels about 120 px, and a big 300 px throw about 670 px.
  - It bounces off screen edges, losing half its speed each time.
  - It bounces once off the floor if it lands faster than 700 px/s (35% bounce).
  - It bonks on the top of the screen.
  - The tilt springs back upright the short way.
- Thrown faster than 900 px/s: a scream. Landing faster than 1100 px/s: dizzy for 2.4 s (stars circle its head). (The stars have their own variable names: reusing the window's `cx, cy` there once moved where its feet sit in the window, and it sank half into the floor.)
- **Parachute:** opens when falling faster than 150 px/s with more than 260 px (`CHUTE_HEIGHT`) still to go. It then falls at 110 px/s, drifting side to side. The 36-block red and white canopy has 4 strings to its raised hands and head.

**Standing on windows:**
- `list_platforms()` lists visible, normal app windows front to back (not minimized, maximized, cloaked, tool windows, click-through overlays, the desktop or taskbar, or the pet's own), at least 150×100 px. It uses the compositor's visible edges (`DwmGetWindowAttribute` 9) because `GetWindowRect` includes invisible borders.
- The list is refreshed every 0.2 s while it's falling, held, or standing on a window.
- While falling, if it passes a window's top edge with its middle more than 12 px inside the window (and nothing in front covers that spot), that window becomes its floor (`plat`, `plat_box`). Each refresh moves it with the window. If the window is gone, or it walks or slides past the edge, it falls.
- The parachute decision measures to the next ledge below, not the taskbar.

**Worried face:** open eyes plus two short slanted eyebrows on the lower half of row 0.

**Per-monitor scaling:** `GetDpiForMonitor` gives each screen's scaling (`Screen.dpi`), and the size used is `scale × that screen's dpi`. Moving to a monitor with different scaling resizes it once.

**Keyboard shortcuts:** a background thread registers them with `RegisterHotKey` and runs its own message loop. Presses come back to the main thread through a queue.

**Notifications:** a Windows toast sent through PowerShell (`Windows.UI.Notifications`), in the background, with no console window.

**Sounds:** made the first time they're needed, using maths (sine sweeps, a wobbly sawtooth scream, a noise whoosh), into `%TEMP%\claude_pet_sounds\<sound>_<volume>.wav`. Played with `winsound`, asynchronously. Windows' simple player has no volume control, so each volume level gets its own quieter copy of the file.

**Error log:** `log_error()` appends a time stamp and traceback to `pet_errors.log`, trimming to the newest half when it's over `ERROR_LOG_KB`. Tk callback errors, log-reading errors, notification and sound errors, and crashes all go there. Each entry's first line ends with the pet's version and Python version (so line numbers can be matched to the right code), and Tk errors say what the pet was doing (`doing: walk`). Under it, `where:` names the last line in `pet/` the error went through, and `values there:` lists that function's local values: numbers, `True`/`False`/`None` as they are, everything else only as its type and size (`str of 13`, `list of 2`), so no text (the login token, chat lines) can get in. The same error (same type and `where`) again in one run is written only as a one-line "again (N times so far)" on the 2nd, 4th, 8th... time (`SEEN_ERRORS`), so a ticking error can't flood the log. Known limit: a repeat that comes back hours later is only noted on those counts.

**Settings window:** a borderless window drawn on one canvas (see the version 6.0 entry in `CHANGELOG.md` for the full design).
- A darker sidebar with the search box and seven pages (`SettingsWindow.PAGES`); on the right the page title, then each section from `sections()` as a heading (with "Reset") over a rounded card.
- Each row is a dict from `row()`: **toggle** (an orange switch; the whole row is clickable), **choice** (a segmented control, beside the label when it fits, below it when it doesn't), **slider**, or a special row (preview, sounds, keys, login, diary, perf, about). A row's `show` hides it until it matters.
- The descriptions come from `TIPS` in `pet/tips.py`. Search matches a row's label, description, section, page, options and extra `words`.
- Resizable (800–1100 wide, starting at 820; 800 so the diary's longest row, "Jumps to windows" with "9,999 made · 9,999 missed", fits in its column), scrolls, and works from the keyboard (Tab, arrows, Space/Enter, Ctrl + F).

**Right-click menu:** a small borderless window drawn the same way (`PopupMenu`): Refresh now, Play fetch, Quiet for an hour / Talk again, Settings, a divider, Quit (`items()`). It highlights the row under the mouse. When you right-click the mascot, it opens to the mascot's right (or left if there's no room), level with its feet, so it never covers the mascot. Opening it closes an unpinned details panel, and hovering doesn't open the panel while the menu is open (the panel used to pop up over the menu and catch its clicks). It's moved with `move_window()`, which checks the window really arrived and uses `SetWindowPos` if Tk held the move back (that was why the menu only worked once). Ten times a second it checks for a mouse press outside itself (`GetAsyncKeyState`) and closes if it finds one. Esc closes it too.

**Dancing:** a 5% chance whenever it stops walking (or when it's bored). It lasts 3.5–6 s. The beat is 0.25 s: arms up left, down, up right, both up. It bops down on beats 2 and 4 and sways half a block, with music notes floating up.

**Single instance:** a named mutex, `claude-usage-pet`. A second start opens the named event `claude-usage-pet-summon` (`SUMMON_EVENT`) and sets it, then quits; the running pet checks it 10 times a second (`WaitForSingleObject` with no wait) and comes over.

**Tray icon (`pet/tray.py`):** its own thread registers a window class and makes a hidden window (not message-only, so it also hears `TaskbarCreated` when Explorer restarts and puts the icon back), then runs a message loop. `Shell_NotifyIconW` adds the icon with a callback message; button-up clicks go to a queue the pet reads 10 times a second. The icon is the 16×16 mascot in `ICON`, drawn at 32×32 into a 32-bit DIB with alpha and made with `CreateIconIndirect`; the corner dot uses the usage colour of the higher limit and is redrawn when it changes. The tooltip (up to 127 characters) has both limits, any error and "quiet for now". Quitting removes the icon.

**Being called over:** `come_here()`. Same monitor, on the taskbar and within 500 px (`COME_DROP`): it sprints there at 5× walking speed (`SPRINT`, the `goto_x` / `chase()` code, which ignores the personality). Otherwise it's placed in the air above the mouse, `CHUTE_HEIGHT` + 90 px above the floor, falling at 200 px/s, so the parachute opens; it waves when it lands.

**Auto-hiding taskbar:** `SHAppBarMessage(ABM_GETSTATE)` says if it auto-hides. If so, `autohide_floors()` looks at every `Shell_TrayWnd` / `Shell_SecondaryTrayWnd` rectangle: one that's at least half the screen wide, reaches the screen's bottom and has slid up into view makes its top that screen's floor (`wb`). Hidden, it leaves the floor at the screen bottom.

**Fetch:** the ball (`BALL`, drawn at 3 px blocks) is a `Sprite` window. Gravity as for the mascot, bounces off the screen's sides and top (60%) and the floor (50%, until it's slower than 140 px/s), then rolls with 750 px/s² friction. The mascot chases with `goto_x` following the ball, picks it up within 26 px, then runs to the mouse and drops it. Dragging the ball and letting go throws it with 70% of the mouse speed (up to 2200 px/s).

**The UFO:** a timeline in `fun.py` (`UFO_BEAM` … `UFO_END`): flies in for 1.5 s, beam on, lifts the mascot 56 px into the saucer over 2 s, keeps it 2 s, drops it, then flies off up and to the right. The saucer (`UFO`, drawn at double block size) is fixed on the screen while the mascot's window moves, so it's drawn at an offset worked out from the mascot's height. The beam is a polygon with Tk's `gray50` stipple: every other pixel is the see-through key colour, so it looks like light. The usage bubble steps aside and speech goes above the saucer.

**The cat:** a `Sprite` that walks along the taskbar of the mascot's screen at 60 px/s with two leg frames (`CAT_A`, `CAT_B`, flipped when walking left), stops 2.5 s when it reaches the mascot, and runs at 200 px/s after a click.

**Settings file:**
- `pet_settings.json` holds:
  - `scale`, `x` and `y`
  - on/off switches: `walk`, `jump`, `naps`, `anim`, `wizard`, `warn`, `cc_app`, `hide_fs`, `one_monitor`
  - `poll`, the refresh time in seconds (120/180/240/300)
  - `notify`, `sounds`, `hotkeys`, `platforms` (on/off) and `volume` (0–100)
  - `warn_at` (70/75/80/85) and `panic_at` (85/90/95), the yellow and red ring levels
  - `bubble` ("both" / "5h" / "hover") and `bubble_style` ("numbers" / "bars")
  - `chatter` ("off" / "some" / "lots")
  - the panel's `panel_tab` ("plan" / "cc" / "sessions"), `plan_chart` ("5h" / "7d"), `cc_view` and `cc_range`
  - `tray`, `pace_warn`, `seasonal`, `quiet_hours`, `dnd`, `rare`, `apprentices`, `bedtime` (on/off), `quiet_from` (20–23 or 0) and `quiet_to` (6–9), the quiet hours, and `bedtime_at` (20–23, 0 or 1), when the pajamas go on
- It's written to a temporary file first, then swapped in, so a crash can't leave half a file.
- Bad or missing values fall back to the defaults.

**Start with Windows:**
- Makes a shortcut named `Claude Usage Pet.lnk` in `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup`.
- The shortcut targets the `pyw` launcher if it's on the path (it picks the newest Python, so it survives Python updates), otherwise this Python's `pythonw.exe`. The script path is its argument.

## Setup

- Windows 10 or 11 (tested on Windows 11).
- Python 3.10 or newer with tkinter (tested with Python 3.14). The older Pythons the Python install manager offers (`py install 3.10`, and other "legacy" versions) come **without tkinter**, so they can't run it: the start-up check says to install the newest Python. On 3.10 every file compiles and nothing newer than 3.10 is used, but the windows themselves haven't been run on it. No pip installs. Runs on 3.14 (Tk 8.6) and 3.15 (Tk 9.0). Tk 9.0 leaks memory for every deleted canvas item, so all canvases are `ui.Canvas`, which reuses items instead (see 7.4 in the change log). New windows should use it too. The code's syntax was checked down to 3.8, but nothing older than 3.14 has been run.
- Claude Code installed and signed in on the same computer.
- The development computer has two 1920×1080 monitors side by side, with the taskbar at the bottom of both.
- Everything specific to one computer (paths, monitors, the Python install) goes in `docs/LOCAL_NOTES.md`, which git ignores.

## GitHub

- The repo is `claude-usage-pet`, and it's **public**. Anything pushed can be copied, so keep personal details out.
- Commits use the GitHub no-reply email, set for this repo only, so no personal email is in the history. Commit times are in UTC (`+0000`) so they don't hint at a location: commit with the `TZ=UTC` environment variable set (in Git Bash: `TZ=UTC git commit ...`).
- Pull requests aren't accepted (`CONTRIBUTING.md`); issues are. Security reports go through GitHub's private vulnerability reporting (`SECURITY.md`).

**Releases:** tag `vX.Y` on `main` and publish a GitHub release for it; the README's download links and release badge follow `releases/latest` by themselves. The notes have: what's new since the last release, Install, Good to know (unofficial, undocumented endpoint, the login only goes to api.anthropic.com), a link to the change log, and end with "If the pet makes you smile, a ⭐ on GitHub helps other people find it." (the same line is under the README's first picture and at its end, and Settings > About links to the repo as "Star it on GitHub").

## Status

**Tested on 2026-10-09** with fake numbers and screenshots on the real screens:
- See-through background, standing on the taskbar, walking frames.
- Details panel fading in, with rounded corners.
- Poke: heart, happy face and hop.
- Sleeping with z's.
- Sweat drop at 90% (replaced in version 3.1 by the warning sign and red ring, tested at 90% and 96%).
- Waving on hover.
- Panel opening on hover and closing after the mouse leaves (with a pretend mouse position).
- Hover-only bubble.
- Animations off.
- Error bubble at 2x.
- Jump height (exactly 34 px).
- Frame timing: steady at about 60 fps, about 0.1 ms of work per frame.
- Hiding during full screen on the second monitor and coming back afterwards.
- Walking from the second monitor onto the main one.
- Seven simulated monitor layouts: level, lower, higher, too high, one-monitor mode, full-screen neighbour, and a bigger monitor on the left.
- CPU: about 4% of one core while walking, about 2% while standing.

**Version 4, tested on 2026-10-09** (second monitor, fake plan numbers):
- Grabbed by the arm, it hangs sideways (90°) and swings.
- A throw from the second monitor onto the main one, with a scream.
- The parachute opening on a long fall.
- Dizzy stars after a hard landing.
- Dancing.
- 100%: black ring with silver edge, slumped with tired eyes.
- Panel the same height (320×343) on both tabs.
- Refresh setting saved.
- The earlier speech, wizard, milestone, memory and monitor tests still pass.

**Version 3, tested on 2026-10-09:**
- Speech bubbles: typing out, wrapping, and staying above the usage bubble.
- Wizard hat, wand and sparkles, with working mode starting and stopping on its own.
- Bars-style bubble.
- Claude Code tab: Overview and Models, read from the real logs.
- Plan tab with the "today" line.
- 50% milestone line.
- Reset cheer with three hops.
- 10th-poke line.
- Memory saved, reloaded and checked.
- No errors.

**Version 5, tested on 2026-10-09** (second monitor):
- Landing on a real window from another program, riding it when it moved, and falling when it closed.
- The parachute only on long drops.
- Worried face after a tool error.
- Faded "15m old" bubble.
- An immediate re-check when the login file changes.
- Error log.
- Generating all 5 sounds (not played).
- Ctrl + Alt + P hiding and showing.
- The settings window.
- Projects view and cost line.
- One real notification.
- Both monitors read as 100% scaling.
- The earlier throw, parachute, monitor, speech, wizard and memory tests still pass.

**Version 5.1, tested on 2026-10-09:**
- The new right-click menu: opening upward, hover highlight, "Settings" opening the window, closing on an outside click.
- All five settings tabs.
- A switch, a choice button and the volume slider, each changed and saved, with the sample file made at 25%.

**Version 5.4, tested on 2026-10-09** (second monitor, real windows from a second program):
- Dragging the window it stands on: it stayed exactly in place on the window, 0 px drift per frame.
- A window sliding over it: pushed along, at most 4 px overlap for a frame.
- Cornered at the screen edge: dropped through to the taskbar.
- A window suddenly brought to the front over it: scooted out the nearer side within 0.4 s.
- Not tested: dragging a real app's window by its title bar with the mouse (the test moved windows by code).

**Version 5.5, tested on 2026-10-09** (second monitor, real windows):
- Jumps from the taskbar: easy window (150 px up) 5/6 made it, medium (280 up) 5/6, too high (390 up) 0/6, each with a line before and an excuse or a brag after.
- Window to window (220 px up): 4/5 made it.
- Small talk over 20 simulated minutes at "Sometimes": about 16 lines, matching what it's doing (walking, dancing, standing on a window, idle), with no repeats.
- The version 5.4 window tests still pass.

**Version 5.6, tested on 2026-10-09** (second monitor, real windows):
- Taskbar: a window sliding in pushed it from x −1220 to −1450 (at most 17 px overlap for a frame); squeezed into the screen edge it stayed put on the floor.
- Leap of faith off a window 520 px up: dove head first, landed in hay, popped out onto the floor (screenshots checked).
- Personalities over 3 simulated minutes: Parkour! 73% walking / 15 hops / 0 naps, Lively 64% / 10 / 0, Normal 41% / 7 / 3, Chill 24% / 4 / 6, Statue 0% / 0.
- Settings: the Personality row (five pills) fits and switches.
- The 5.4 and 5.5 window and jump tests still pass.

**Version 5.7, tested on 2026-10-09** (second monitor, real windows):
- Jumping for a window that's too high, from beside it: hit the side every time (8/8), for windows that end above the taskbar and ones that go behind it, then landed beside it with no overlap.
- The same jump from in front of a window that goes behind the taskbar: landed back in front and stayed (not pushed).
- A window ending exactly at the taskbar slid over it: pushed. One that goes behind the taskbar: not pushed.
- Success rates now that the side counts: 150 px up 10/10, 280 px up 7/12, 390 px up 0/6. Window to window 5/5.

**Version 7.0, tested on 2026-10-10** (a separate test pet with scratch settings, memory, error log and cache, fake usage numbers and made-up Claude Code logs, on the second monitor; Python 3.15, and 3.14 for imports and the UFO):
- Screenshots: the Sessions tab, the new menu, all four outfits (Halloween, Christmas, New Year, Valentine's), fireworks, the shiny colour, the spell tome with two apprentices (three busy sessions), the wand with one session, eyes following a pretend pointer left, right-and-up and down, the UFO arriving, lifting and gone, the cat meeting the mascot, the ball in flight, the quiet line and menu, the new settings rows on every page, and the Pet diary.
- Being called over: a run of 300 px, a parachute drop 800 px away, a drop onto the other monitor and back. A real second start (a separate process setting the summon signal) brought it over. A real Ctrl + Alt + H press called it (the real running pet held P and D, so those showed "another app").
- Fetch: the chase, "got it!", grabbing the ball back from the mascot by pretend mouse drag, and a throw that crossed to the other monitor (it followed).
- The tray icon: added, tooltip with both limits, a pretend left click called the mascot, a right click opened the menu at the pointer, switching it off removed it.
- Quiet mode from the menu (speech and sounds blocked, back after "Talk again"), and quiet hours at eight different times, across and not across midnight.
- The early pace warning (70% with 3 hours left): one line and one notification, and not again on the next check. Session wrap-ups: two finished sessions as one "while you were away" line.
- "Service changed": the bubble, the panel, and the error log listing only the names it got.
- The log cache on the real logs: the same numbers after a restart, which read in 0.04 s instead of 0.25 s. With 64 KB chunks: every answer read, a 300 KB line skipped, a deleted log throwing the cache away, and only new lines read after a restart.
- `autohide_floors()` with made-up taskbar positions (hidden, slid up, on one of two monitors, on the side). The forecast gives the same answer as before. The tour, all five lines in order.

**Not tested yet (version 7.0):**
- A real auto-hiding taskbar (this computer doesn't have one), and Windows' Do Not Disturb (Windows 11 may not report it to apps at all; presentation mode should).
- Real mouse clicks on the tray icon (tested with pretend clicks), and Explorer restarting with the icon showing.
- The meow and the other sounds actually heard, and the seasons on their real dates.
- Real Claude Code reading tools and parallel sessions triggering the tome and the apprentices (tested by setting what the log reader saw).
- The rare events on their real timers (tested by starting them directly).

**Not tested yet:**
- Real API data inside the pet.
- Wizard mode triggered by real Claude Code activity (it was tested by calling it directly).
- The quiet-time comments and random quotes on their real timers.
- Real mouse hover, click, drag and throw. These were tested with pretend mouse events.
- Sounds actually playing, the "good morning" and late-night lines (time-dependent), and a monitor at a different scaling.
- Ctrl + mouse wheel.
- Start with Windows.
- Real YouTube, Netflix or game full screen. This was tested with a stand-in full-screen window.
- Display scaling above 100%.
- An auto-hiding taskbar.
- A taskbar on the side of the screen.

**Known limits:**
- With an auto-hiding taskbar it stands on the screen's bottom edge and rides up when the taskbar slides up (not tried on a real one yet).
- Windows plays one sound at a time, so a new sound cuts off the last one (dance music included).
- If a monitor has different display scaling, the pet keeps its size in real pixels, so it looks smaller or bigger there.
- No automatic login refresh: the pet only notices when Claude Code renews the login. Doing the renewal itself would mean sending the refresh token to Anthropic's login server (not api.anthropic.com) and could clash with Claude Code, so it's left out unless you decide otherwise.
- Claude Code stats only cover this computer's logs. If Claude Code deletes old logs, they disappear from the stats too.

**Ideas for later:**
- Things to do when idle: 7.3 replaced the 7.2 ones with sweeping, painting, fishing, balloons and a paper plane; the rest of the list in the 7.1 entry in `CHANGELOG.md` are still ideas.
