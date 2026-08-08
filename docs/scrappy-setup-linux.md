# Scrappy (MX Linux) Setup

Scrappy is `192.168.1.214` on the LAN (hostname `mx.mynet`). It is reachable
but SSH is currently closed, so copy-paste these blocks on the machine itself.

Laptop Tailscale IP: `100.100.66.117`
Desktop scheduler (OFFLINE, needs new dongle): `100.69.113.41`

---

## Step 1 — Enable SSH (so we can push commands to Scrappy remotely)

```bash
sudo apt update
sudo apt install -y openssh-server
sudo systemctl enable --now ssh
sudo ufw allow ssh        # if ufw is active
```

After this, from the laptop you can run:
`ssh scrappy@192.168.1.214`

---

## Step 2 — Install Tailscale

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

Log in with the kooshikooo-lab account when it prints the auth URL.
Then check: `tailscale status`

---

## Step 3 — Install Ollama (runs Gemma locally on Scrappy)

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull gemma3:4b
```

Test it:
```bash
ollama run gemma3:4b "Reply with exactly the word OK"
```

List what's running: `ollama ps`

---

## Step 4 — Join the Dask cluster (once desktop is back online)

Desktop's scheduler is `tcp://100.69.113.41:8786`. When it's reachable again:

```bash
python -m pip install dask distributed
python scripts/spawn_worker.py tcp://100.69.113.41:8786 scrappy
```
