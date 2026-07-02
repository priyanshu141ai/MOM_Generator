$profile = "$env:LOCALAPPDATA\Google\Chrome\User Data"
$chrome = "C:\Program Files\Google\Chrome\Application\chrome.exe"
Start-Process $chrome -ArgumentList @(
  "--remote-debugging-port=9222",
  "--user-data-dir=$profile",
  "--profile-directory=Default",
  "https://accounts.google.com/"
)
