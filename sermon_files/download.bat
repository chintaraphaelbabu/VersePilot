@echo off
cd /d "%~dp0"

yt-dlp ^
  -N 4 ^
  --download-archive downloaded.txt ^
  --download-sections "*01:00:00-inf" ^
  -f "ba[ext=m4a]/ba" ^
  --extract-audio ^
  --audio-format m4a ^
  -o "video\%%(upload_date)s - %%(title)s [%%(id)s].%%(ext)s" ^
  --match-filter "duration >= 3600 & id != K5pwxV5dcG4 & id != PECZxPTQWdo" ^
  "https://www.youtube.com/@TeluguGilgalAGChurch/streams"

pause