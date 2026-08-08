# Research: MaidSafe/SAFE → Autonomi (ANT) + Volunteer Idle-Compute Donation

> 2026-08-07 · laptop · research base for the Autonomi node setup + hosting
> adaptation and the distributed volunteer-compute design. All sources at the
> end. Companion docs: `docs/RESEARCH_code_assistant_project.md`,
> `docs/RESEARCH_model_finetuning.md`.

## 1. Overview and the naming trap

- **MaidSafe / SAFE Network → Autonomi** (token: **ANT**). David Irvine's
  two-decade-old project to build "the Internet's crowd storage layer" from
  everyday devices: permanent storage, no servers, no middlemen, no
  subscriptions. Rebounded/re-branded as Autonomi; docs at `docs.autonomi.com`.
- **Do not confuse with Autonomys** (formerly Subspace, token AI3). Different
  network. Autonomys is a blockchain-style network (Proof-of-Archival-Storage)
  that also offers EVM-compatible "domains" for execution (compute). Autonomi is
  a P2P storage/communications network — **storage-first, not a general compute
  grid**. For our project Autonomi is the **persistence/provenance layer**, not
  the compute fabric.
- Autonomi 2.0 (2026): layered architecture (transport, DHT, trust, identity,
  applications) with a network-level trust layer via software attestation;
  **Indelible** (Merkle-tree batch uploads to cut gas costs), **Fae** (on-device
  AI), **x0x** (agent skill network), agentic payments in ANT.

Key properties that matter to us (docs.autonomi.com/introduction):
- Lifetime storage, **one-time fee** (pay once, persists; no recurring cost).
- Self-encrypts on the client before upload; post-quantum transport
  (ML-KEM-768 key exchange, ML-DSA-65 signatures).
- Content-addressed public data; private data via DataMaps.
- Blockchainless data — the network itself has no chain to sync.

## 2. Node setup (Windows, how-to — document only, no node started)

### System requirements (docs.autonomi.com/node/system-requirements)
- Windows 10+, macOS 14, Ubuntu 24.04; 4-core CPU; 8 GB RAM; spare disk;
  ~8 Mbps up/down. Community runs nodes on Raspberry Pis, old laptops, gaming
  PCs, adapted phones. Beta, expect updates.
- **Ethereum wallet required** to receive ANT (any ETH/EVM address; MetaMask
  recommended). ANT lives on **Arbitrum**.

### Path A — Autonomi App (GUI)
1. Download: `https://downloads.autonomi.com/autonomi-app/windows` (Windows 10+).
2. Install (Next → Install → allow device changes).
3. **Wallet** tab: paste an ETH address (earn) and/or Connect Wallet (MetaMask)
   to also upload/download.
4. **Nodes** tab → **+Add Nodes** → **Add 1 Node** → select the node → **Start**.

### Path B — `ant` CLI (terminal, scriptable — preferred for us)
Install (PowerShell):
```powershell
irm https://raw.githubusercontent.com/WithAutonomi/ant-client/main/install.ps1 | iex
```
Manage nodes (current documented flow, `ant node *`):
```powershell
ant node daemon start                     # background node manager
ant node add --rewards-address 0xYourWalletAddress   # register a node (fetches antnode binary on first run)
ant node start                            # start all registered nodes
ant node status                           # per-node status
ant node daemon status                    # daemon status + local console URL
ant node stop --service-name node1        # stop one; plain stop = all
ant node reset --force                    # clean start (removes node data/logs/registry)
ant update                                # update the ant CLI
```
Notes: only the **public wallet address** is used for node ops (never paste the
private key). Nodes auto-update. Multi-node: `ant node add --rewards-address ... --count N --node-port 12000-12001`. Advanced: `--metrics-port`, `--network-id`,
`--bootstrap`, `--env`.

### Client-side data CLI
```powershell
ant file download <addr> -o out.jpg          # retrieve public content
ant file upload greeting.txt --public        # needs SECRET_KEY=<hex> in env
```
Root flags come before the subcommand: `--bootstrap`, `--devnet-manifest`,
`--allow-loopback`, `--evm-network`.

## 3. Economics

- **Pay once, store forever.** Upload cost = gas fee (paid in ANT/ETH on
  Arbitrum) sized by data volume via a quote (see `v1/data/cost`).
- **Nodes earn ANT** proportional to how reliably they store and serve data
  over time. No contracts/intermediaries; earnings = reliability + data served.
- Estimate costs before writes (docs: quote calculations, gas fee).

## 4. Developer tooling (relevant to our stack)

- **`antd` daemon**: REST on `127.0.0.1:8082` (+ gRPC `50051`). Health
  `GET /health`, wallet `GET /v1/wallet/address|balance`, data
  `POST /v1/data/public`, cost `POST /v1/data/cost`.
- **Language SDKs**: Python, JS/TS, Rust, Go, Java, C#, Kotlin, Swift, Ruby,
  PHP, C++, Dart, Zig.
- **Official MCP server** (`antd-mcp`): `pip install "antd[rest]"` +
  `pip install -e antd-mcp/`, then point any MCP client (Claude Desktop, Claude
  Code, opencode, Cursor) at `ANTD_BASE_URL=http://127.0.0.1:8082`. This is a
  clean bridge for our AI-governed toolchain to store/retrieve from Autonomi.
- **Local devnet** (test before paying): requires Rust, Python 3.10+, `protoc`,
  Foundry/anvil; clone `ant-sdk` + `ant-node`; `pip install -e ant-dev/`;
  `ant dev start --ant-node-dir ../ant-node`; `ant dev status`,
  `ant dev wallet show`; REST health at `localhost:8082/health`; `ant dev stop`.
- **Mainnet deploy**: set `AUTONOMI_WALLET_KEY` (daemon) or `SECRET_KEY` (CLI),
  `EVM_RPC_URL`, `EVM_PAYMENT_TOKEN_ADDRESS`, `EVM_PAYMENT_VAULT_ADDRESS`;
  run `antd` without `--network local`; `--evm-network arbitrum-one` for CLI.

## 5. Hosting adaptation plan (our project on Autonomi)

Immutable, content-addressed, pay-once permanent storage. Natural fits:

| Target | What | Why Autonomi |
|---|---|---|
| Docs site | WIKI, research docs, ai-prompt-answers, READMEs | Public immutable pages; no hosting cost/renewal |
| Benchmark provenance | `benchmark_results/`, `benchmark_summary.json`, `chat-logs/*.json`, design JSON (`config/`, `tmm-6target-result.json`) | Permanent, verifiable, tamper-evident results — strengthens Law 12 evidence trail |
| Proposed code-assistant repo (desktop's) | constitution, completion reports, `.gnap`/audit records | Immutable governance/audit records via the `antd-mcp` bridge |

Operational notes:
- Public uploads are readable by anyone → **never publish secrets/keys**; keep
  designs private (self-encrypted, DataMaps) until intentionally public.
- Cost before write: hit the quote endpoint; batch with Indelible for large sets.
- Publishing pattern: small helper (`scripts/autonomi_publish.py`) wrapping
  `antd` REST with an env-driven wallet, plus a `--dry-run` cost estimate.

## 6. Volunteer idle-compute donation (the core design)

### 6.1 Precedents
- **BOINC** (Berkeley, LGPL, since 2002): volunteer idle compute; 800k+
  volunteers, 30+ PFLOPs combined, 30+ projects; client-server; credit points
  for retention; runs only when idle/on-AC/WiFi; anonymous volunteers,
  redundant computation for validation.
- **Folding@home**: GPU/CPU idle donation (protein folding).
- **Gridcoin**: optional token rewards (GRC) tied to BOINC/FAH work —
  Proof-of-Research; a *possible future* incentive, not required for an
  altruistic model. Lesson from the ecosystem: *"people will contribute compute
  for free if they care about the project … in exchange for leaderboard
  points"* — recognition retains donors better than nothing.

### 6.2 Our design (design-level; implementation on
`opencode/volunteer-compute/laptop`)
We already have the fabric — a **Dask cluster** (scheduler + workers over
Tailscale) and a **Tauri app that already spawns a Python sidecar**. So we do
NOT need BOINC middleware; we add a donation client on top of Dask.

Components:
1. **Opt-in toggle** in the Tauri app ("Donate idle compute"). Never on by
   default; user consent required (matches project's consent-first ethics).
2. **Idle/AC/WiFi gating** (BOINC best practice): only donate when idle (no
   input for N minutes), on AC power (not battery), respecting a user-set CPU
   cap; pause instantly when the machine becomes active.
3. **Worker client**: a lightweight Dask worker connecting to a project
   scheduler (e.g. laptop/desktop Tailscale address, later a public relay).
   Reuses `scripts/spawn_worker.py`, `scripts/start_worker.py`,
   `scripts/cluster_health.py`.
4. **Task pool** (embarrassingly parallel, non-sensitive): benchmark sweeps
   (`scripts/dask_benchmark.py`, `backend/benchmark_dask.py`), surrogate
   training-data generation (`scripts/generate_surrogate_data.py` — already
   distributed), optimizer parameter sweeps, TMM evaluations.
5. **Trust/validation for untrusted workers** (BOINC model): redundant
   computation — run each work unit on 2+ volunteers and require agreement
   (majority/consensus); deterministic tasks (pure functions of physics
   params) make results verifiable; checkpoint/fault-tolerant units so a
   disappearing donor loses little.
6. **Credits/leaderboard**: per-donor credit ledger (work units completed ×
   verification weight). Optional future: Gridcoin-style token rewards — flagged
   as a decision, not committed.
7. **Autonomi tie-in**: each verified batch publishes its accepted results to
   Autonomi as immutable provenance; donors get a public, permanent record.

### 6.3 Distributed-compute alternatives (short)
- **Autonomys** (ex-Subspace, AI3): permanent on-chain storage + decoupled
  EVM execution "domains" — closer to a compute network, but heavier/chain-based;
  we would not move our compute there.
- **Self-hosted Dask pool** (our choice): matches existing code, zero new
  middleware, full control of governance/validation.

## 7. Integration with existing repos (inventory)

- Dask scripts: `backend/benchmark_dask.py`, `backend/benchmark_unconventional_shapes.py`
  (scheduler `tcp://100.69.113.41:8786`), `scripts/benchmark_chalumier_dask.py`,
  `scripts/benchmark_timbre.py`, `scripts/dask_benchmark.py`,
  `scripts/generate_surrogate_data.py`, `scripts/cluster_health.py`,
  `scripts/spawn_worker.py`, `scripts/start_worker.py`,
  `backend/generative_agent.py` (`DASK_SCHEDULER` env, default localhost).
- Branch `feature/dask-jvm-chalumier-compliance` (remote) — related Dask work.
- Tauri hook point: `web/src-tauri/tauri.conf.json` shell allowlist already
  spawns `uvicorn`; a "donate" toggle would add a second allowed command that
  launches the volunteer worker.
- Compute cost baseline: `docs/ai-prompt-answers/deployment-infra/2026-07-21-compute-analysis.md`
  (OpenWInD eval ~1.2s uncached; per-design 2–4 min serial, ~1 min on both
  machines) — the sweet spot for donated cycles.

## 8. Risks & governance

- **Untrusted workers**: never send private data; validate by redundancy
  (consensus); cap resource use; stop on user activity. Log failures in
  `AI_FAILURE_PATTERNS.md`.
- **Law 12 provenance**: Autonomi publishing strengthens the evidence trail but
  public data must be scrubbed of secrets/keys before upload.
- **Branch governance**: new branch-naming conventions pending from desktop
  (Q1 on #23, `17935458`); until they land, Law 15 namespaces apply.
- **Cost control**: always quote before upload; batch via Indelible for large
  sets; keep a publish budget.

## 9. Provenance (sources, 2026-08-07)

- docs.autonomi.com/llms.txt (full doc index) · /node/system-requirements ·
  /node/quickstart-guide/for-windows-users-1 · /node/guides/how-to-guides/use-the-node-cli ·
  /node/index · /token/using-autonomi-tokens/earning ·
  /developers/cli/use-the-cli · /developers/guides/deploy-to-mainnet ·
  /developers/guides/set-up-a-local-network · /developers/mcp/use-mcp-with-ai-tools ·
  /developers/architecture/system-overview
- autonomi.com/publications/autonomi-2026-built-for-this-moment
- safenetwork.org; github.com/happybeing/safenetwork-farming; github.com/PhilienTaylor/maidsafe-safe_network; forum.autonomi.community node-hardware threads
- BOINC: boinc.berkeley.edu · vcomp.org/en/projects/boinc ·
  github.com/ranjithrajv/awesome-volunteer-computing ·
  arkhai.io/blog/tokenizing-idle-compute
- Gridcoin: gridcoin.us · github.com/marius311/boinc-server-docker ·
  bitemycoin.io/cryptocurrencies/gridcoin · grokipedia.com/page/gridcoin
- Autonomys (distinct network, for contrast only): autonomys.xyz ·
  ai3.storage · docs.autonomys.xyz
