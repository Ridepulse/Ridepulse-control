# Sporting
All in one control software for home-matches at Daknam <br />
Combines previous software packages into one. <br /> <br />
3 Video output's are needed: <br />
  1: Controlpanel <br />
  2: Scoreboard output <br />
  3: Led boarding output <br />
The correct screen can be edited in the config file.

# Important notes:
 ❗ Main.mp4 and Gameday.mp4 are needed in the main folder for the boarding to work (working on a way to import them).
 ❗ DMG needs to be manually put in the folder 'Scorebord' because the file size is too large for GitHub.
  
# Functions
 ✅ config.json includes settings for the displays, Spotify playlists, duration of scorebord sponsors, if the greg visual should be played in min 4 and the layout of the scoreboards (font, size, etc).
  <br /> ✅ Proper error handling is mostly implemented with warning boxes.
  <br /> ✅ Opening other necessary software should work, ledset needs to open with admin rights.
  <br /> ✅ Line up can be put in, to start the cursor needs to be in the last box and then enter needs to be pressed.
  <br /> ✅ Import en export mogelijk van sponsoren voor het scorebord mogelijk gemaakt vanuit controlpanel, bij het verwijderen worden sponsoren gearchiveerd naar Scorebord_archive.
  <br /> ✅ Startuur van de match kan ingegeven worden bovenaan. Dit update de verschillende timings van audio.
  <br /> ✅ Most of the functions can be executed with different keyboard buttons.
  <br /> ✅ Visual of Greg is being displayed automaticly in min. 4, this time in right resolution.
  <br /> ❗ It is possible to render loops in software, still need to change file location of the loop to the right folder.
  <br /> ✅ Fade in/out function excists.
  <br /> ❌ config aanpassen in software zelf.

# Bugs:
✅ LED Boarding feed sluit niet goed af. => resolved.
  <br /> ❗ De top playlist klikt niet in het juiste label, stop werkt totaal niet tho (opent ook een ander vlc window ofzo). => Top video playlsit is uit de code gehaald. Kunnen nu evt greg label gebruiken?
  <br /> ❌ Rendering.exe Werkt niet, opent nieuwe instantie van Ridepulse system (possible solution: exe van maken en die runnen? werkt voorlopig niet tho)
  <br /> ❌ Makkelijkere manier vinden om presets toe te voegen. (Mss via config file?)
  <br /> ✅ RESET NAAR STACK VAN SCOREBORD IPV LINEUP OF GOAL KNOP!! + BUG ALS GREG AFGELOPEN IS! => Bug has been resolved. 
  <br /> ❗ Extra tijd visuals?
  <br /> ✅ 15 minuten timer voor half time => implemented, maar lelijk!
  <br /> ❌ (Mss gewoon verschillende VLC vensters die een single loop afspelen voor led boarding?)
  <br /> ❌ Flash bij switchen tussen video en afbeelding en bij 2 videos na elkaar (sponsor)
  <br /> ❌ Implement more Ridepulse :)
  
# This is still a work in process...

