# Protocol lifecycle note

The `status: draft_pre_freeze` field inside `config/certificate_v1_1_fixed_n100.yaml`
records the configuration's state when the protocol source was prepared. It is not
the campaign's final lifecycle authority. The configuration became immutable when
the protocol was frozen at commit `b7b8ad451a69e7951e121b3d7ac86c97e116d3ab`.

The authoritative lifecycle records are:

- `protocol/FROZEN_PROTOCOL.json` for the pre-run freeze;
- `FINAL_RUN_MANIFEST.json` for the completed fixed-design campaign; and
- `GATE_STATUS.json` for the final promotion decision.

This note resolves the apparent naming mismatch without changing a frozen input or
invalidating its recorded SHA-256 hash.
