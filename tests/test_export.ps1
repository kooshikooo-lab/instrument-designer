# Test the pyinstaller-built backend binary

# Start the backend
$process = Start-Process -FilePath "C:\instrument-designer\dist\instrument-backend.exe" -WindowStyle Hidden -PassThru
Start-Sleep -Seconds 5

# Test POST export with proper JSON
$json = '{"preset":"koncovka_C"}'
$response = curl.exe -X POST http://127.0.0.1:8000/export/cadquery -H "Content-Type: application/json" -d $json 2>&1
Write-Host "Response: $response"

# Also test with konkovka_C (typo check)
$json2 = '{"preset":"konkovka_C"}'
$response2 = curl.exe -X POST http://127.0.0.1:8000/export/cadquery -H "Content-Type: application/json" -d $json2 2>&1
Write-Host "Response 2: $response2"

# List available instruments again to check names
$instruments = curl.exe -s http://127.0.0.1:8000/export/cadquery/instruments 2>&1
Write-Host "Instruments: $instruments"

# Kill the backend process
Get-Process -Name "instrument-backend" -ErrorAction SilentlyContinue | Stop-Process -Force