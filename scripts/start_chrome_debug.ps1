$profile = "$env:LOCALAPPDATA\Google\Chrome\User Data"
$chrome = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$profileDirectory = if ($args.Count -gt 0) { $args[0] } else { "Profile 2" }
Start-Process $chrome -ArgumentList @(
  "--remote-debugging-port=9222",
  "--user-data-dir=$profile",
  "--profile-directory=$profileDirectory",
  "https://accounts.google.com/"
)
