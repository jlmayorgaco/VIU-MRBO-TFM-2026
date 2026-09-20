"""Primary supported-load Cargo campaign infrastructure."""

from .campaign import CampaignResult, run_campaign, run_campaign_file
from .config import CampaignConfig, GUARDS, load_config
from .design import RunSpec, WorldSpec, build_run_specs, build_worlds
from .guards import GuardDecision, evaluate_guard
from .preflight import (
    PreflightAttestation,
    PreflightEvidenceError,
    validate_preflight_evidence,
)

__all__ = [
    "CampaignConfig",
    "CampaignResult",
    "GUARDS",
    "GuardDecision",
    "PreflightAttestation",
    "PreflightEvidenceError",
    "RunSpec",
    "WorldSpec",
    "build_run_specs",
    "build_worlds",
    "evaluate_guard",
    "load_config",
    "run_campaign",
    "run_campaign_file",
    "validate_preflight_evidence",
]
