$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$Py = "C:\Users\Admin\AppData\Local\Programs\Python\Python314\python.exe"
$OutDir = Join-Path $Root "test_output\testing"
New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
$Log = Join-Path $OutDir "dask_scheduler.log"
"===== started $(Get-Date -Format 'yyyy-MM-ddTHH:mm:ss') =====" | Add-Content $Log
& $Py -m distributed.cli.dask_scheduler --host 100.69.113.41 --port 8786 *>> $Log
"===== exited =====" | Add-Content $Log
exit 0
