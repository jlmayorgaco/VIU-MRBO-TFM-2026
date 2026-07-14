"""Integrated physical-coalition certificate campaign."""

from .model import CertificateStage, FailureCode, PhysicalWorld, PROTOCOL_VERSION
from .runner import (
    analyze_campaign,
    extend_by_precision,
    finalize_manifest,
    freeze_protocol,
    prepare_protocol,
    render_figures,
    run_dry_run,
    run_official,
)

__all__ = [
    "CertificateStage",
    "FailureCode",
    "PhysicalWorld",
    "PROTOCOL_VERSION",
    "prepare_protocol",
    "run_dry_run",
    "freeze_protocol",
    "run_official",
    "extend_by_precision",
    "analyze_campaign",
    "render_figures",
    "finalize_manifest",
]