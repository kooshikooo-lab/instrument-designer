# Linux Deployment Research (2026-07-20)

## Why Linux for This Project

### Parallelization Speed (Primary Reason)
- **Windows**: Uses `spawn` — creates fresh Python interpreter per worker, requires pickle/unpickle of entire problem object
- **Linux**: Uses `fork` — copy-on-write memory, near-instant process creation, no serialization needed
- **Measured impact**: Fork is ~20x faster at process startup (2ms vs 40ms per process)
- **Our benchmark**: Windows parallel = 1.67x speedup. Linux fork = estimated 3-5x

### Process Startup Comparison
| Method | Startup Time | Pickle Required | Thread Safe |
|--------|-------------|-----------------|-------------|
| spawn (Windows) | ~40ms | Yes | Yes |
| fork (Linux default) | ~2ms | No | No |
| forkserver (Python 3.14+) | ~5ms | No | Yes |

### Fork vs Spawn Technical Details
- **fork**: Uses `os.fork()` system call, copies parent process memory via copy-on-write
  - Child inherits all parent's modules, variables, objects in memory
  - No pickle overhead — objects accessible via memory copy
  - Unsafe with threads (locks from parent can deadlock in child)
  - NumPy starts thread pool on import → potential issues
- **spawn**: Starts fresh Python interpreter from scratch
  - Re-imports all modules, reconstructs all objects
  - Requires everything to be picklable
  - Safe, cross-platform, slower
- **forkserver** (Python 3.14): Pre-forks a clean server process at startup
  - New workers fork from this clean server (no thread issues)
  - Fast startup like fork, safe like spawn
  - Best of both worlds

### Python 3.14 Changes
- Default start method on Linux changes from `fork` to `forkserver`
- Reason: fork's thread-safety issues with NumPy, Matplotlib, etc.
- forkserver avoids these while maintaining performance
- Our code should work with both (no fork-specific assumptions)

## Deployment Options

### WSL2 (Quickest Test)
- `wsl --install` in PowerShell
- Ubuntu automatically installed
- All Python deps work on Linux
- Fork parallelization works immediately
- Can test speedup in ~10 minutes

### Docker Container (Recommended for Server)
- Reproducible environment
- Easy deployment and scaling
- Good for team access
- Can be deployed to any cloud provider

### Native Linux (Best Performance)
- Full kernel access
- Maximum CPU/memory utilization
- No WSL2 virtualization overhead
- Good for dedicated server

## Server Requirements
- **Minimum**: 2 cores, 4GB RAM
- **Recommended**: 4-8 cores, 8GB RAM (for parallel optimizer)
- **Cost**: $5-10/month VAWS VPS
- **OS**: Ubuntu LTS (22.04 or 24.04)
- **Python**: 3.12+ (3.14 when stable for forkserver)

## Code Changes Needed
Minimal — our code already supports `n_workers` parameter:
- On Linux: `multiprocessing.get_context('fork')` instead of `spawn`
- No `if __name__` guard needed (but doesn't hurt)
- Pool creation is 20x faster
- No pickle serialization overhead

## Impact on Project Timeline
- **Immediate**: Can test optimizer speedup with WSL2 (no commitment)
- **Short-term**: Set up Docker container for server deployment
- **Long-term**: Python 3.14 migration for forkserver benefits

## Key Sources
- Python docs: multiprocessing start methods
- Stack Overflow: fork vs spawn performance
- pymoo docs: parallelization strategies
- Python 3.14 release notes: forkserver default
