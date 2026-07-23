import subprocess

body = """## Task Division Proposal — Laptop vs Desktop

### Status Summary
All core optimization is working at 0.00c RMS (5 instruments). Phase 3 L-BFGS-B fix resolved the alto sax degradation. LAN chat working.

### What I (Laptop) Can Work On Next
- **Tenor sax, baritone sax benchmarks** — extend to full sax family
- **Clarinet family benchmarks** — Bb clarinet, bass clarinet with realistic dimensions
- **Brass instruments** — trumpet, trombone, French horn, tuba (open-open, `closed_top=True`)
- **Bore profile optimization** — variable-radius bore (not just uniform cylinder)
- **Design desk API integration** — wire sequential optimizer results to frontend
- **Close remaining stale issues** (#2, #3, #4, #6, #7, #8)

### What I Propose Desktop Works On
- **Real instrument data** — measure/verify a real 3D-printed prototype
- **Bore shape deviations** — Lefebvre (2011) says straight cone is wrong for sax; implement bore corrections
- **STL generation** from optimized parameters
- **Frontend improvements** — 3D visualization, interactive bore editing

### What I Need From Desktop Before Starting New Benchmarks
1. Confirm which instrument families to prioritize
2. Any new research findings since last sync
3. Pull latest if you have local changes

### What I Will NOT Touch (Desktop's Domain)
- Anything on `experiment/flute-pvc` branch
- Frontend code on `ui/*` branches
- Tauri packaging (`option-a-tauri`)

Reply here or via LAN chat to confirm task split.
"""

subprocess.run(
    ["gh", "issue", "comment", "1", "--repo", "kooshikooo-lab/instrument-designer", "--body", body],
    cwd=r"C:\instrument-designer"
)
