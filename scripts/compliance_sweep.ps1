$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$Py = "C:\Users\Admin\AppData\Local\Programs\Python\Python314\python.exe"
$OutDir = Join-Path $Root "test_output\testing"
New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
$Log = Join-Path $OutDir "compliance_sweep.log"
$Ts = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
"===== $Ts =====" | Add-Content $Log
& $Py (Join-Path $Root "scripts\compliance_watchdog.py") --once *>> $Log
"EXIT $LASTEXITCODE" | Add-Content $Log
exit 0
