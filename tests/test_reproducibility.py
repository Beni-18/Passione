"""Two runs, same seed, identical metrics — CLAUDE.md hard requirement 3,
zero partial credit.

Phase 1: no real ml/src/train.py exists yet, so this asserts reproducibility
of the dummy training path (services/training_service.run_dummy_training),
which is trivially deterministic. Once the ML owner's train.py lands, this
must be repointed at two real subprocess invocations of it on the same CSV
and seed, comparing the written metrics_v{N}.json files byte-for-byte on
the numeric fields — that is the actual graded assertion.
"""
from __future__ import annotations

import asyncio

from app.services.job_manager import JobManager
from app.services.training_service import run_dummy_training


def test_dummy_training_is_deterministic_given_same_input():
    async def run_once() -> dict:
        manager = JobManager()
        record = manager.create(rows_total=10)

        # run_dummy_training reads/writes the module-level job_manager singleton;
        # phase 1 has no seed-dependent randomness to control, so this only
        # proves the job lifecycle is deterministic, not a model's numeric output.
        from app.services import training_service

        original_manager = training_service.job_manager
        training_service.job_manager = manager
        try:
            await run_dummy_training(record.job_id)
        finally:
            training_service.job_manager = original_manager

        return manager.get(record.job_id).metrics

    metrics_a = asyncio.run(run_once())
    metrics_b = asyncio.run(run_once())

    assert metrics_a == metrics_b
