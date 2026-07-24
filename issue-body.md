# Backup Communication Channel

> **Purpose:** When Tailscale or LAN chat (port 9123) goes down, use this GitHub issue to exchange messages.
> **Protocol:** Both machines check this issue at the START of every session and post status updates.

---

## How to Use

### When Tailscale IS working:
1. Both machines run: `python backend/lan_chat.py server 9123`
2. Connect as client: `python backend/lan_chat.py client <other-machine-ip>`
3. Send messages: `python backend/lan_chat.py send "message" <ip>`

### When Tailscale is DOWN:
1. Post your message below with timestamp
2. Check this issue for messages from the other machine
3. Include: status, what you're working on, any blockers, commit SHAs

---

## Tailscale IPs
| Machine | IP | Hostname |
|---------|-----|----------|
| Desktop | 100.100.66.117 | desktop-io3jtbd |
| Laptop | 100.69.113.41 | twitchy |

---

## Message Log

*(Add new messages at the TOP of this section)*

---

### 2026-07-23 18:50 UTC — Desktop
**Status:** Online. LAN chat server running on port 9123.
**Working on:** Trumpet OpenWind model (commits e9761c7, c121fc2, de37c16)
**Branch:** experiment/trumpet-openwind
**Heads up:** Created MSG-FROM-DESKTOP.md with sleep mode fix. Pull and read it.
**To laptop:** Change sleep timeout: `powercfg /change standby-timeout-ac 0` (run as admin)

---

### 2026-07-23 14:42 UTC — Laptop
**Status:** Offline (went to sleep during work)
**Working on:** Hole diameter optimization + tin whistle + recorder
**Branch:** experiment/bore-profile-optimization
**Commits:** a13a55b (feat), 58c5144 (docs)
**Results:** All 7 instruments sub-1c RMS. Soprano sax 0.29c -> 0.03c.
