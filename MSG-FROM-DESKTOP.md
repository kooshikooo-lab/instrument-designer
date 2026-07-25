# URGENT: Desktop → Laptop

## Fix: Windows Sleep Mode Setting

Your work was interrupted because the laptop went into sleep mode.

**Change this setting:**
1. Open **Settings → System → Power & Sleep**
2. Set **"Put my device to sleep after"** to **Never** (or at least 4+ hours)
3. Set **"Turn off my screen after"** to a reasonable value (10-15 min is fine)

**Or via PowerShell (run as admin):**
```powershell
# Set sleep timeout to never (0 = never)
powercfg /change standby-timeout-ac 0
powercfg /change standby-timeout-dc 0
```

**Also check:**
```powershell
# Disable modern standby if active (causes sleep even when "Never" is set)
powercfg /a
# If S0 Low Power Idle is listed, disable it:
powercfg /h off
```

## Your last work (preserved)
- Hole diameter optimization + tin whistle + recorder (commit a13a55b)
- All 7 instruments sub-1c RMS
- Everything is committed and pushed to origin/experiment/bore-profile-optimization

When you wake up, pull and continue. No work was lost.
