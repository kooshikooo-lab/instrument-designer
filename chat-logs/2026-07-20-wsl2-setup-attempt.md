# WSL2 Setup Attempt (2026-07-20)

## What Happened

### Step 1: Install WSL
- Ran `wsl --install` via elevated PowerShell
- WSL2 installed successfully (default version: 2)

### Step 2: Blocker — Virtualization Disabled
- `wsl --status` reports:
  - "WSL2 is unable to start since virtualization is not enabled on this machine."
  - "Please ensure the 'Virtual Machine Platform' optional component is enabled and virtualization is turned on in your computer's firmware settings."
- Ran `wsl --install --no-distribution` (elevated) to enable Virtual Machine Platform Windows feature
- Still blocked: BIOS virtualization (Intel VT-x / AMD-V) must be enabled first

### Status: DEFERRED
- BIOS virtualization settings too difficult to navigate with damaged keyboard
- Saved for later — will revisit when keyboard is fixed or BIOS path is known
- Alternative plan: use `concurrent.futures.ProcessPoolExecutor` on Windows to avoid fork/spawn issue entirely

### What the Test Will Do (After BIOS Fix)
1. `wsl --install -d Ubuntu` — installs Ubuntu distribution
2. Launch WSL, set up Python venv
3. Copy project files to WSL filesystem (`/home/user/instrument-designer/`)
4. Install dependencies: `pip install pymoo openwind scipy numpy`
5. Run benchmark: serial vs parallel (fork context)
6. Compare with Windows parallel benchmark (1.67x speedup)

### Expected Results
- **Windows spawn parallel**: 1.67x speedup (measured)
- **Linux fork parallel**: 3-5x speedup (estimated)
- **Linux forkserver (Python 3.14)**: 3-5x speedup + thread safety

### Files to Copy to WSL
- `C:\instrument-designer\backend\optimizer.py`
- `C:\instrument-designer\test_parallel.py`
- `C:\instrument-designer\quick_test.py`
- `C:\instrument-designer\profile_single.py`

### Notes
- WSL2 uses Hyper-V under the hood → requires hardware virtualization
- WSL1 doesn't need virtualization but is slower and not recommended
- If BIOS virtualization can't be enabled (some OEMs lock it), alternative: Docker Desktop with WSL2 backend, or native Linux install
