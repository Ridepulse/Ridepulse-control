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
  <br /> ✅ Fix line up => werkt normaal wel nu, mits een kleine flits bij het afspelen van een goal visual.
  <br /> ✅ Import en export mogelijk van sponsoren voor het scorebord mogelijk gemaakt vanuit controlpanel, bij het verwijderen worden sponsoren gearchiveerd naar Scorebord_archive.
  <br /> ✅ Startuur van de match kan ingegeven worden bovenaan. Dit update de verschillende timings van audio.
  <br /> ❌ Match bediening met knoppen op toetsenbord? WIP
  <br /> ❌ Na goal automatisch in tekst veld gaan van de goal? WIP


# Bugs:
✅ LED Boarding feed sluit niet goed af. => resolved.
  <br /> ❗ De top playlist klikt niet in het juiste label, stop werkt totaal niet tho (opent ook een ander vlc window ofzo). => Top video playlsit is uit de code gehaald.
  <br /> ❌ Functie creeren om main.mp4 en gameday.mp4 te renderen vanuit deze software met rendering code. => Werkt niet, opent nieuwe instantie van Ridepulse system (possible solution: exe van maken en die runnen)
  <br /> ❌ Makkelijkere manier vinden om presets toe te voegen. (Mss via config file?)
  <br /> ✅ RESET NAAR STACK VAN SCOREBORD IPV LINEUP OF GOAL KNOP!! + BUG ALS GREG AFGELOPEN IS! => Bug has been resolved. 
  <br /> ❗ Extra tijd visuals?
  <br /> ✅ 15 minuten timer voor half time => implemented, maar lelijk!
  <br /> ❌ (Mss gewoon verschillende VLC vensters die een single loop afspelen voor led boarding?)
  <br /> ❌ Flash bij switchen tussen video en afbeelding en bij 2 videos na elkaar (sponsor)
  <br /> ❌ Clear all fields bij lineup button.
  <br /> ✅ Als lineup gespeeld heeft dan wordt greg niet getoond maar de laatse video van de lineup. => resolved door een nieuwe stack te gebruiken voor deze visual only. HEEFT NIET DE JUIST GROOTTE!!!!
  <br /> ❌ Implement more Ridepulse :)
  
# This is still a work in process...

