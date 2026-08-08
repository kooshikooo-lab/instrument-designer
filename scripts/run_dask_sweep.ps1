param(
    [string]$Presets = "d_whistle",
    [int]$Workers = 1
)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$Py = "C:\Users\Admin\AppData\Local\Programs\Python\Python314\python.exe"
$OutDir = Join-Path $Root "test_output\testing"
New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
$Log = Join-Path $OutDir "dask_sweep.log"
$Err = Join-Path $OutDir "dask_sweep.err"
Remove-Item $Log, $Err -ErrorAction SilentlyContinue
$Proc = Start-Process -FilePath $Py -ArgumentList @(
    (Join-Path $Root "scripts\benchmark_chalumier_dask.py"),
    "--workers", "$Workers",
    "--presets", $Presets
) -WorkingDirectory $Root -RedirectStandardOutput $Log -RedirectStandardError $Err -PassThru -NoNewWindow
"PID $($Proc.Id) | presets=$Presets workers=$Workers" | Set-Content (Join-Path $OutDir "dask_sweep.pid")
$Proc.WaitForExit()
"EXIT $($Proc.ExitCode)" | Add-Content $Log
exit $Proc.ExitCode
