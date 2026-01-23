# Sporting
All in one control software for home-matches at Daknam <br />
Combines previous software packages into one. <br /> <br />
3 Video output's are needed: <br />
  1: Controlpanel <br />
  2: Scoreboard output <br />
  3: Led boarding output <br />
The correct screen can be edited in the config file.

# Important notes:
 ❗ Main.mp4 and Gameday.mp4 are needed in the Rendering_boarding folder, this is also the place where the rendering function saves them.
 ❗ DMG needs to be manually put in the folder 'Scorebord' because the file size is too large for GitHub.

# Keyboard shortcuts:
ESC: Exits a text field
<br />Backspace: Stops all local media
<br />Space: Play/pause Spotify
<br />Keypad 1-9: Play different playlist or sounds (following the list in the software)
<br />Pg up: Goal home
<br />Pg down: remove goal home
<br />Arrow left: previous song (Spotify)
<br />Arrow right: next song (Spotify)
<br />Arrow up: Fade in
<br />Arrow down: Fade out
<br />T: Start timer
<br />L: Enter lineup field
<br />G: Enter goal field
<br />F1: Reset clock 00:00
<br />F2: Reset clock 45:00
<br />F9: Boarding: Main
<br />F10: Boarding: Gameday
<br />F11: Boarding: Reset
<br />F12: Boarding: Render new loop (to do)
<br />Q: Exit



# Functions:
 ✅ config.json includes settings for the displays, Spotify playlists, duration of scorebord sponsors, if the Greg visual should be played in min 4 and the layout of the scoreboards (font, size, etc).
  <br /> ✅ Proper error handling is mostly implemented with warning boxes.
  <br /> ✅ Opening other necessary software should work, ledset needs to open with admin rights.
  <br /> ✅ Line up can be put in, to start the cursor needs to be in the last box and then enter needs to be pressed.
  <br /> ✅ Import en export mogelijk van sponsoren voor het scorebord mogelijk gemaakt vanuit controlpanel, bij het verwijderen worden sponsors gearchiveerd naar Scorebord_archive.
  <br /> ✅ Starting time of the match can be put in via the box, this updates the ques for the audio.
  <br /> ✅ Most of the functions can be executed with different keyboard buttons.
  <br /> ✅ Visual of Greg is being displayed automatically in min. 4, this time in right resolution.
  <br /> ✅ It is possible to render the different loops in the software.
  <br /> ✅ Fade in/out function exists.
  <br /> ✅ Config can be edited by clicking a button in the software, this will open Notepad.
  <br /> ✅ 15 minute timer for half time counts down when the playlist is started.
  <br /> ❌ Implement intern media circuit (F5-F8)
  <br /> ❌ Autoplay alle muziekbestanden-buttons?
  <br /> ❌ Extra tijd visuals?



# Bugs:
✅ LED Boarding feed sluit niet goed af. => resolved.
  <br /> ❗ De top playlist klikt niet in het juiste label, stop werkt totaal niet tho (opent ook een ander vlc window ofzo). => Top video playlsit is uit de code gehaald. Kunnen nu evt greg label gebruiken?
  <br /> ❌ Makkelijkere manier vinden om presets toe te voegen. (Mss via config file?)
  <br /> ❌ Flash bij switchen tussen video en afbeelding en bij 2 videos na elkaar (sponsor)

# This is still a work in process...

