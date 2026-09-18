"""Assemble rendered PDF pages into numbered visual-QA contact sheets."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Directory containing page-*.jpg")
    parser.add_argument("output", type=Path, help="Destination directory")
    parser.add_argument("--pages-per-sheet", type=int, default=20)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pages = sorted(args.source.glob("page-*.jpg"))
    if not pages:
        raise SystemExit(f"No rendered pages found in {args.source}")
    if args.pages_per_sheet < 1:
        raise SystemExit("--pages-per-sheet must be positive")

    columns = 5
    rows = math.ceil(args.pages_per_sheet / columns)
    cell_width, cell_height = 200, 295
    args.output.mkdir(parents=True, exist_ok=True)

    for sheet_index, offset in enumerate(range(0, len(pages), args.pages_per_sheet), 1):
        sheet = Image.new("RGB", (columns * cell_width, rows * cell_height), "white")
        draw = ImageDraw.Draw(sheet)
        for slot, page_path in enumerate(pages[offset : offset + args.pages_per_sheet]):
            page_number = int(page_path.stem.rsplit("-", 1)[1])
            x = (slot % columns) * cell_width
            y = (slot // columns) * cell_height
            with Image.open(page_path) as rendered:
                page = rendered.convert("RGB")
                page.thumbnail((190, 268))
                sheet.paste(page, (x + (cell_width - page.width) // 2, y + 20))
            draw.text((x + 4, y + 3), str(page_number), fill="black")
        sheet.save(args.output / f"contact-{sheet_index:02d}.jpg", quality=90)

    print(f"contact sheets: {math.ceil(len(pages) / args.pages_per_sheet)}")


if __name__ == "__main__":
    main()
