# Test the pyinstaller-built backend binary

# Start the backend
$repo = Split-Path $PSScriptRoot -Parent
$process = Start-Process -FilePath "$repo\dist\instrument-backend.exe" -WindowStyle Hidden -PassThru
Start-Sleep -Seconds 5

# Test health endpoint
try {
    $health = curl.exe -s http://127.0.0.1:8000/health
    Write-Host "Health check: $health"
} catch {
    Write-Host "Health check failed: $_"
}

# Test export endpoint
try {
    $export = curl.exe -s http://127.0.0.1:8000/export/cadquery/instruments
    Write-Host "Export instruments: $export"
} catch {
    Write-Host "Export instruments failed: $_"
}

# Test POST export
try {
    curl.exe -X POST http://127.0.0.1:8000/export/cadquery -H "Content-Type: application/json" -d '{"preset":"koncovka_C"}' -o test.stl
    if (Test-Path "test.stl") {
        $size = (Get-Item test.stl).Length
        Write-Host "STL file size: $size bytes"
        if ($size -gt 1000) {
            Write-Host "SUCCESS: STL file is valid (> 1000 bytes)"
        } else {
            Write-Host "FAIL: STL file is too small ($size bytes)"
        }
    } else {
        Write-Host "FAIL: STL file not created"
    }
} catch {
    Write-Host "POST export failed: $_"
}

# Kill the backend process
Get-Process -Name "instrument-backend" -ErrorAction SilentlyContinue | Stop-Process -Force