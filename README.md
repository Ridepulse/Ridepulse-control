# Sporting

All in one control software for home-matches at Daknam 
Combines previous software packages into one. 

3 Video output's are needed: 
1: Controlpanel 
2: Scoreboard output 
3: Led boarding output 

The correct screen can be edited in the config file.

# Important notes:
❗ Main.mp4 and Gameday.mp4 are needed in the Rendering\_boarding folder, this is also the place where the rendering function saves them.
❗ DMG needs to be manually put in the folder 'Scorebord' because the file size is too large for GitHub.

# Keyboard shortcuts:
ESC: Exits a text field
Backspace: Stops all local media
Space: Play/pause Spotify
Keypad 1-9: Play different playlist or sounds (following the list in the software)
Pg up: Goal home
Pg down: remove goal home
Arrow left: previous song (Spotify)
Arrow right: next song (Spotify)
Arrow up: Fade in
Arrow down: Fade out
T: Start timer
L: Enter lineup field
G: Enter goal field
F1: Reset clock 00:00
F2: Reset clock 45:00
F9: Boarding: Main
F10: Boarding: Gameday
F11: Boarding: Reset
F12: Boarding: Render new loop (to do)
Q: Exit

# Functions:
✅ config.json includes settings for the displays, Spotify playlists, duration of scorebord sponsors, if the Greg visual should be played in min 4 and the layout of the scoreboards (font, size, etc).
✅ Proper error handling is mostly implemented with warning boxes.
✅ Opening other necessary software should work, ledset needs to open with admin rights.
✅ Line up can be put in, to start the cursor needs to be in the last box and then enter needs to be pressed.
✅ Import en export mogelijk van sponsoren voor het scorebord mogelijk gemaakt vanuit controlpanel, bij het verwijderen worden sponsors gearchiveerd naar Scorebord\_archive.
✅ Starting time of the match can be put in via the box, this updates the ques for the audio.
✅ Most of the functions can be executed with different keyboard buttons.
✅ Visual of Greg is being displayed automatically in min. 4, this time in right resolution.
✅ It is possible to render the different loops in the software.
✅ Fade in/out function exists.
✅ Config can be edited by clicking a button in the software, this will open Notepad.
✅ 15 minute timer for half time counts down when the playlist is started.
❌ Implement intern media circuit (F5-F8)
❌ Autoplay alle muziekbestanden-buttons?
❌ Extra tijd visuals?

# Bugs:
✅ LED Boarding feed sluit niet goed af. => resolved.
❗ De top playlist klikt niet in het juiste label, stop werkt totaal niet tho (opent ook een ander vlc window ofzo). => Top video playlsit is uit de code gehaald. Kunnen nu evt greg label gebruiken?
❌ Makkelijkere manier vinden om presets toe te voegen. (Mss via config file?)
❌ Flash bij switchen tussen video en afbeelding en bij 2 videos na elkaar (sponsor)
❌ Render new loop werkt weer niet... zucht

# This is still a work in process...

