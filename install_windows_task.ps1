param(
  [Parameter(Mandatory=$true)]
  [string]$ProjectDir,

  [string]$TaskName = "WeChatDailyReportChecker",
  [string]$Time = "20:00",
  [switch]$EnableSend
)

$ErrorActionPreference = "Stop"

$project = Resolve-Path $ProjectDir
$python = Join-Path $project ".venv\Scripts\python.exe"
$settings = Join-Path $project "settings.yaml"
$employees = Join-Path $project "employees.yaml"

if (-not (Test-Path $python)) {
  throw "Python venv not found: $python"
}
if (-not (Test-Path $settings)) {
  throw "Missing settings file: $settings"
}
if (-not (Test-Path $employees)) {
  throw "Missing employees file: $employees"
}

$args = "-m wechat_daily_report --settings `"$settings`" --employees `"$employees`""
if ($EnableSend) {
  $args += " --send"
}
$action = New-ScheduledTaskAction -Execute $python -Argument $args -WorkingDirectory $project
$trigger = New-ScheduledTaskTrigger -Daily -At $Time
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel LeastPrivilege
$settingsObj = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settingsObj -Force | Out-Null
$mode = if ($EnableSend) { "send enabled (configuration gates still apply)" } else { "dry-run preview" }
Write-Host "Installed scheduled task '$TaskName' at $Time in $mode mode."
