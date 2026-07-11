$env:Path = "C:\Users\koosh\AppData\Local\Programs\Python\Python312;" + $env:Path
Set-Location "C:\instrument-designer"
Write-Host "Starting Instrument Designer Backend on port 8000..."
python -m uvicorn backend.server:app --port 8000 --reload
