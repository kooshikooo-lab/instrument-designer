param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("low", "medium", "heavy")]
    [string]$Tier
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Py = "C:\Users\Admin\AppData\Local\Programs\Python\Python314\python.exe"
$OutDir = Join-Path $Root "test_output\testing"
New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
$Log = Join-Path $OutDir "sweep_$Tier.log"

& $Py (Join-Path $Root "scripts\run_all_tests.py") --tier $Tier *>> $Log
exit $LASTEXITCODE
