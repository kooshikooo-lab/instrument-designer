# Test the pyinstaller-built backend binary

# Start the backend
$process = Start-Process -FilePath "C:\instrument-designer\dist\instrument-backend.exe" -WindowStyle Hidden -PassThru
Start-Sleep -Seconds 5

# Test POST export with proper JSON escaping
$json = '{"preset":"koncovka_C"}'
curl.exe -X POST http://127.0.0.1:8000/export/cadquery -H "Content-Type: application/json" -d $json -o "C:\instrument-designer\test.stl" 2>&1

# Check STL file
if (Test-Path "C:\instrument-designer\test.stl") {
    $size = (Get-Item "C:\instrument-designer\test.stl").Length
    Write-Host "STL file size: $size bytes"
    if ($size -gt 1000) {
        Write-Host "SUCCESS: STL file is valid (> 1000 bytes)"
    } else {
        Write-Host "FAIL: STL file too small ($size bytes)"
    }
} else {
    Write-Host "FAIL: STL file not created"
}

# Kill the backend process
Get-Process -Name "instrument-backend" -ErrorAction SilentlyContinue | Stop-Process -Force