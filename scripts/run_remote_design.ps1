param(
    [string]$Presets = "d_whistle"
)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$Py = "C:\Users\Admin\AppData\Local\Programs\Python\Python314\python.exe"
$OutDir = Join-Path $Root "test_output\testing"
New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
$Log = Join-Path $OutDir "remote_design.log"
Remove-Item $Log -ErrorAction SilentlyContinue
& $Py (Join-Path $Root "scripts\chalumier_design_remote.py") --presets $Presets *>> $Log
"EXIT $LASTEXITCODE" | Add-Content $Log
exit 0
