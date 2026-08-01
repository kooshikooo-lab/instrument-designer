# QUARANTINED 2026-07-31: references backend.tmm_optimizer_sequential, deleted
# from backend/archived_optimizers (docs/ARCHIVED_OPTIMIZERS.md). Superseded by
# backend/two_phase_optimizer.py. Kept for reference; not collected by pytest.
try:
    import backend.tmm_optimizer_sequential  # noqa: F401
except ModuleNotFoundError:
    raise SystemExit(
        "ARCHIVED: backend.tmm_optimizer_sequential was deleted on 2026-07-31 "
        "(see docs/ARCHIVED_OPTIMIZERS.md). Superseded by backend/two_phase_optimizer.py."
    )
print("Import OK")