param(
    [int]$Workers = 6,
    [int]$Threads = 2,
    [string]$Mem = "2.5GB"
)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$Py = "C:\Users\Admin\AppData\Local\Programs\Python\Python314\python.exe"
& $Py (Join-Path $Root "scripts\start_desktop_cluster.py") --workers $Workers --threads $Threads --mem $Mem
exit $LASTEXITCODE
