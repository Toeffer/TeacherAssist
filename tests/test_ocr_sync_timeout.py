"""The synchronous compatibility endpoint must not wait for a timed-out worker."""

from __future__ import annotations

import threading
import time

import pytest

from teacherassist_core.ocr.engines import FakeEngine
from teacherassist_core.ocr.pipeline import OCRBusy, PipelineConfig, process_single_image_sync
from teacherassist_core.ocr.types import OCRStatus


def test_sync_timeout_returns_while_worker_slot_remains_occupied(monkeypatch):
    import teacherassist_core.ocr.pipeline as pipeline

    release = threading.Event()

    def blocked(*args, **kwargs):
        release.wait(2)
        raise RuntimeError("controlled worker finished")

    monkeypatch.setattr(pipeline, "process_document", blocked)
    config = PipelineConfig(require_engines=())
    try:
        started = time.monotonic()
        result = process_single_image_sync(b"image", config=config, engines=[FakeEngine("tesseract", "x")], timeout_s=0.02)
        assert time.monotonic() - started < 0.5
        assert result.status is OCRStatus.FAILED
        assert result.error and "Zeit" in result.error
        with pytest.raises(OCRBusy):
            process_single_image_sync(b"image", config=config, engines=[FakeEngine("tesseract", "x")], timeout_s=0.02)
    finally:
        release.set()
        time.sleep(0.05)
