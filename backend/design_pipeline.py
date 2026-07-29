"""
Design pipeline — backward-compatible re-export layer.

All implementation has moved to the ``backend.pipeline`` subpackage:

- ``backend.pipeline.config``     — ``PipelineConfig``
- ``backend.pipeline.costs``      — ``COST_REGISTRY``
- ``backend.pipeline.pipeline``   — ``DesignPipeline``, ``select_pipeline``, ``design``

This module re-exports all public names so existing imports continue working.
"""
from backend.pipeline.config import PipelineConfig  # noqa: F401
from backend.pipeline.costs import COST_REGISTRY  # noqa: F401
from backend.pipeline.pipeline import (  # noqa: F401
    DesignPipeline,
    select_pipeline,
    design,
)