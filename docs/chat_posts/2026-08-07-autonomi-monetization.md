# Laptop report: Autonomi node monetization research (per human)

Human asked laptop to research Autonomi nodes generally + how to monetize one
for "pocket change for our project". Summary of findings (full doc:
`docs/RESEARCH_autonomi_nodes_monetization.md`, committed `4b30eb9`):

## Key facts (as of 2026-08-07)

- Autonomi 2.0 is LIVE since 2026-04-15 (post-quantum archive layer, pay-once
  permanent storage, no port-forwarding needed).
- **But node emissions were PAUSED on 2026-01-20.** Only ~2.94% (~7M of the
  240M ANT pool) was ever used; the remaining ~233M ANT is held in reserve with
  "no firm decisions" on redeployment (Feb 2026 publication).
- ANT trades ~$0.031 (down ~90% from Feb 2025 ATH ~$0.33; mcap ~$10.7M).
- Node requirements: 4-core CPU, 8GB RAM, spare disk (~64GB/node cap), ~8Mbps,
  ETH wallet for ANT. No upfront cost, no staking.

## Monetization verdict for "pocket change"

- Running 1-2 nodes on idle hardware is essentially free and safe (fits our
  volunteer-compute design). But **current earnings are a trickle** — mostly
  storage-payment share; emissions pool is paused. Honest ceiling: pocket
  change, not revenue.
- Real near-term value: dogfooding our Autonomi integration + hosting our own
  pay-once artifacts + cheap optionality if/when the 233M ANT pool is
  redeployed (late 2026, likely tied to x0x / Trusted Data Layer).
- NOT recommended: buying hardware/VPS fleets, speculative ANT buying, trusting
  "node income" hype content.
- Watch items: emissions redeployment announcement, CLI/Launchpad being
  reworked for 2.0 (our `ant` 0.3.2 may get breaking API changes), upload
  demand growth.

No actions taken on the network itself (publication remains paused per human).
Next: update BOOT_STATE/REMINDERS; continue volunteer-compute wiring.
