"""Placeholder keyframe extractor.

This freeze keeps video handling non-destructive.  Use ffmpeg manually or extend
this script when keyframes are required for a specific video set.
"""

from __future__ import annotations


def main() -> int:
    print("Keyframe extraction not run automatically; video catalog was generated without copying MP4 frames.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
