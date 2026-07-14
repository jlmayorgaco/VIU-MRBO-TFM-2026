"""CLI entrypoint for SP5 cooperative payload transport experiments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from viu_mrob_tfm.sp5 import run_payload_transport_config, run_sp5_config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="SP5 YAML config path.")
    args = parser.parse_args(argv)
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if str(config.get("protocol_family", "")) == "payload_transport_v2":
        result = run_payload_transport_config(args.config)
    else:
        result = run_sp5_config(args.config)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
