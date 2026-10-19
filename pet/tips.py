# the descriptions shown next to each option in settings.


# what each setting does (shown under it in the settings window), then its on/off effects or choices
TIPS = {
    "Refresh now": ("Checks your plan usage right away, instead of waiting for the next automatic check.", []),
    "Refresh every": ("How often the mascot checks your plan usage on its own.", [
        ("2 min", "The default. Fresh numbers without asking the usage service too often."),
        ("3–5 min", "Fewer requests and slightly older numbers. Handy if you ever see \"slow down\".")]),
    "Keep details open": ("Pins the details panel above the mascot.", [
        ("On", "The panel stays open until you close it with ×."),
        ("Off", "The panel opens when you hover the mascot and fades away when you move off.")]),
    "Count tokens like the Claude app": ("Chooses how the Claude Code tab counts tokens and picks the peak hour.", [
        ("On", "Matches the Claude desktop app: every logged copy of an answer is added up, and peak hour "
               "is when your sessions start."),
        ("Off", "Real numbers: each answer is counted once (about 3× lower), and peak hour is your busiest hour.")]),
    "Personality": ("How much the mascot moves about. Hover an option to see what it does.", [
        ("Parkour!", "Hardly ever stands still. It runs about fast, jumps from window to window every few seconds, "
                     "dives off window edges into hay, heads off to your other monitors, and always finds a way up "
                     "a ledge or onto a high window (rope, ladder, cannon...). Barely naps."),
        ("Lively", "Walks a lot and a bit faster, jumps to windows nearby, sometimes dives off edges, and often "
                   "climbs up to high windows and other monitors."),
        ("Normal", "A bit of walking, a bit of standing about, the odd jump, nap or trip to another monitor."),
        ("Chill", "Mostly hangs out. Short, slow strolls, rare jumps, rare trips, plenty of naps."),
        ("Statue", "Stays in one spot: no walking, jumping or trips. It still blinks, reacts, hops when poked "
                   "and talks.")]),
    "Walk around": ("Lets the mascot wander along the taskbar.", [
        ("On", "It walks left and right, and across to your other monitors."),
        ("Off", "It stays in one spot, but still blinks, hops and reacts.")]),
    "Jump now and then": ("Random little hops.", [
        ("On", "It hops about every 30 seconds, and now and then jumps over to a window nearby (if Stand on "
               "windows is on). It doesn't always make it."),
        ("Off", "No random hops. It still hops when you poke it or a limit resets.")]),
    "Take naps": ("Lets the mascot fall asleep.", [
        ("On", "It sleeps after 5 minutes away from the computer, wakes when you're back, and takes "
               "short naps now and then."),
        ("Off", "It always stays awake.")]),
    "Wizard when Claude works": ("Wizard mode while your tokens are going up.", [
        ("On", "It puts on a wizard hat and casts sparkles while Claude is working, and reads from a floating "
               "spell tome while Claude reads your files."),
        ("Off", "It carries on as usual while Claude works.")]),
    "Warn when nearly full": ("A coloured ring around the usage bubble when a limit is nearly used up.", [
        ("On", "Yellow ring from your yellow level, red from your red level (see Warning levels), and "
               "black once a limit is completely used up."),
        ("Off", "No ring. The red dot in the bubble and the 90% speech line still show.")]),
    "Warning levels": ("Sets when the warning ring turns yellow and when it turns red.", [
        ("Yellow", "From 70, 75, 80 or 85%."),
        ("Red", "From 85, 90 or 95%.")]),
    "Animations": ("All of the mascot's movement and effects.", [
        ("On", "It walks, hops, blinks, fades and types out its speech."),
        ("Off", "A completely still mascot, instant panels and no typing. Lightest on your computer.")]),
    "Chatter": ("How often the mascot talks in speech bubbles.", [
        ("Off", "It never talks."),
        ("Sometimes", "A line every minute or two about whatever it's up to, plus reactions to what's happening."),
        ("A lot", "About 2.5× more often."),
        ("Non-stop", "Extra extra chatty: about 5× more often. It has a lot to say.")]),
    "Size": ("How big the mascot is, from 0.75x to 3x.", [
        ("Tip", "Ctrl + mouse wheel over the mascot fine-tunes the size.")]),
    "Bubble": ("What the bubble above its head shows.", [
        ("Limits", "Both limits, the 5-hour limit only, or only while you hover."),
        ("Style", "Numbers, or two small bars.")]),
    "Hide during full screen": ("Gets out of the way of videos and games.", [
        ("On", "It fades away while something is full screen on its monitor, and won't walk onto that monitor."),
        ("Off", "It always stays visible.")]),
    "Stay on one monitor": ("Keeps the mascot on one screen.", [
        ("On", "It turns around at the screen's edges. You can still drag it to another screen."),
        ("Off", "It walks across to your other monitors.")]),
    "Start with Windows": ("Starts the mascot automatically.", [
        ("On", "It starts when you sign in to Windows."),
        ("Off", "Start it yourself: double-click Start pet.bat in its folder.")]),
    "Settings…": ("Opens a window with every option in one place, each with a short description.", []),
    "Stand on windows": ("Lets the mascot land on top of your windows, and makes windows solid.", [
        ("On", "When it falls (dropped, thrown or walking off an edge) past the top of a window, it lands there, "
               "rides along if you move the window, and falls off when it closes. Windows in front push it "
               "aside, and if it's cornered it drops down to the taskbar. On the taskbar, windows push it aside too."),
        ("Off", "It only ever stands on the taskbar.")]),
    "Sound effects": ("Turns all of the mascot's sounds on or off. Pick which ones below.", [
        ("On", "Plays the sounds you've picked (quietly, through Windows' normal sound output)."),
        ("Off", "Silent. This is the default.")]),
    "Which sounds": ("Tap a sound to switch it on or off. Switching one on plays it.", []),
    "Desktop notifications": ("Windows notifications for the important moments.", [
        ("On", "A notification at 90% and 100% of a limit, when a nearly-used limit resets, and when your login "
               "expires. Shows even while the mascot is hidden."),
        ("Off", "Only the mascot's own speech bubbles.")]),
    "Keyboard shortcuts": ("Shortcuts that work anywhere in Windows, even when another app is in front.", [
        ("On", "The shortcuts below work."),
        ("Off", "They do nothing, and other apps can use those keys.")]),
    "Shortcuts": ("Click a shortcut, then press the new keys. Esc cancels, Backspace clears it.", []),
    "Quit": ("Closes the mascot. Your settings and its memory are saved first.", []),
    "Volume": ("How loud the sound effects are. You'll hear a sample when you let go.", []),
    "Size": ("How big the mascot is. Ctrl + mouse wheel over it works too.", []),
    "Bubble shows": ("Which limits the bubble above its head shows, or only show it when you hover.", []),
    "Bubble style": ("Numbers, or two small bars.", []),
    "Chat context in bubble": ("How full the latest Claude Code chat's context is, like \"ctx 62%\". It's always "
                               "in the details panel.", [
        ("On", "Shows it while that chat has replied in the last hour."),
        ("Off", "Only the details panel shows it.")]),
    "Clock": ("How times are shown in the details panel, like when a limit resets.", []),
    "Dates": ("Day first or month first, like Fri 16/10 or Fri 10/16.", []),
    "Apprentices for parallel sessions": ("Little apprentice wizards join in when more than one Claude Code "
                                          "session is working at once, one for each extra session (up to 3).", []),
    "Rare surprises": ("Every so often something unusual happens: a cat strolls by, a UFO drops in, or the "
                       "mascot wakes up a rare colour.", []),
    "Seasonal outfits": ("Dresses up for special days: a pumpkin at Halloween, a Santa hat in December, a top "
                         "hat at New Year, a party hat on its birthday, and hearts on Valentine's Day.", []),
    "Pajamas at bedtime": ("Gets ready for bed at night: a blue and white striped nightcap, and a candle "
                           "to light the way.", [
        ("On", "It wears them from the time below until 6 AM. This is the default."),
        ("Off", "No nightcap or candle.")]),
    "Bedtime from": ("When the nightcap and candle come out.", []),
    "Quiet hours": ("No talking and no sounds at night. The usage bubble still shows.", []),
    "Quiet from": ("When quiet hours start.", []),
    "Quiet until": ("When quiet hours end.", []),
    "Follow Do Not Disturb": ("Stays quiet while Windows is in Do Not Disturb, focus or presentation mode "
                              "(if your Windows reports it).", []),
    "Early pace warning": ("Tells you once per window when your pace would use up a limit well before it resets, "
                           "while there's still time to slow down.", []),
    "Tray icon": ("A little mascot by the clock with your usage in its tooltip. Click it to call the mascot over; "
                  "right-click it for the menu.", []),
    "Yellow ring from": ("When the warning ring turns yellow.", []),
    "Red ring from": ("When the warning ring turns red. It turns black at 100%.", []),
}
