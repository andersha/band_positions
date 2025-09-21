#!/usr/bin/env python3
"""Generate absolute placement trajectories per band for the GitHub Pages visualizer."""
from __future__ import annotations

import argparse
import ast
import json
import re
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List

import pandas as pd

DIVISION_ORDER = [
    "Elite",
    "1. divisjon",
    "2. divisjon",
    "3. divisjon",
    "4. divisjon",
    "5. divisjon",
    "6. divisjon",
    "7. divisjon",
]


def slugify(candidate: str, seen: set[str]) -> str:
    """Create a URL-safe slug for the band name."""
    normalized = (
        unicodedata.normalize("NFKD", candidate)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    base = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-") or "band"
    slug = base
    counter = 2
    while slug in seen:
        slug = f"{base}-{counter}"
        counter += 1
    seen.add(slug)
    return slug


def compute_absolute_positions(df: pd.DataFrame) -> tuple[Dict[str, List[dict]], int]:
    """Return a mapping of orchestra name to chronological placement entries."""
    entries_by_band: Dict[str, List[dict]] = defaultdict(list)
    global_max_field = 0

    for year, year_df in df.groupby("year", sort=True):
        counts = year_df["division"].value_counts().to_dict()
        ordered_divisions = [div for div in DIVISION_ORDER if div in counts]
        other_divisions = sorted(div for div in counts if div not in DIVISION_ORDER)
        division_sequence = ordered_divisions + other_divisions

        offsets: Dict[str, int] = {}
        cumulative = 0
        for division in division_sequence:
            offsets[division] = cumulative
            cumulative += int(counts[division])
        global_max_field = max(global_max_field, cumulative)

        division_sizes = {division: int(counts[division]) for division in division_sequence}

        for row in year_df.itertuples():
            offset = offsets[row.division]
            absolute_position = offset + int(row.rank)
            conductor = row.conductor
            if isinstance(conductor, float) and pd.isna(conductor):
                conductor_value: str | None = None
            else:
                conductor_value = str(conductor).strip() or None

            entry = {
                "year": int(row.year),
                "division": row.division,
                "rank": int(row.rank),
                "division_size": division_sizes[row.division],
                "absolute_position": absolute_position,
                "field_size": cumulative,
                "points": float(row.points) if pd.notna(row.points) else None,
                "max_points": float(row.max_points) if pd.notna(row.max_points) else None,
                "conductor": conductor_value,
                "pieces": row.pieces_normalized,
            }
            entries_by_band[row.orchestra].append(entry)

    # Sort chronologically per band
    for entries in entries_by_band.values():
        entries.sort(key=lambda item: item["year"])

    return entries_by_band, global_max_field


def _parse_piece_list(raw: object) -> list[str]:
    """Return the cleaned list of pieces for a placement row."""

    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return []

    text = str(raw).strip()
    if not text:
        return []

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        try:
            parsed = ast.literal_eval(text)
        except (SyntaxError, ValueError):
            parsed = text

    pieces: list[str] = []
    if isinstance(parsed, list):
        for item in parsed:
            if item is None:
                continue
            piece = str(item).strip()
            if piece:
                pieces.append(piece)
    elif isinstance(parsed, str):
        snippet = parsed.strip()
        if snippet:
            pieces.append(snippet)
    elif isinstance(parsed, tuple):
        for item in parsed:
            if item is None:
                continue
            piece = str(item).strip()
            if piece:
                pieces.append(piece)

    return pieces


def load_dataset(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df = df[df["rank"].notna()].copy()
    df["rank"] = df["rank"].astype(int)
    df["year"] = df["year"].astype(int)
    df["division"] = df["division"].astype(str)
    df["orchestra"] = df["orchestra"].astype(str)

    df["pieces_normalized"] = df.apply(
        lambda row: _parse_piece_list(row.get("pieces_list"))
        if "pieces_list" in row
        else _parse_piece_list(None),
        axis=1,
    )

    # Fall back to the free-text column when the structured list is empty.
    mask = df["pieces_normalized"].map(len) == 0
    if "pieces" in df.columns:
        df.loc[mask, "pieces_normalized"] = (
            df.loc[mask, "pieces"].fillna("")
            .map(lambda value: [value.strip()] if str(value).strip() else [])
        )

    return df


def build_payload(df: pd.DataFrame) -> dict:
    entries_by_band, max_field_size = compute_absolute_positions(df)
    seen_slugs: set[str] = set()

    bands = [
        {
            "name": name,
            "slug": slugify(name, seen_slugs),
            "entries": entries,
        }
        for name, entries in entries_by_band.items()
    ]
    bands.sort(key=lambda band: band["name"].lower())

    years = sorted(df["year"].unique().tolist())
    metadata = {
        "years": years,
        "divisions": DIVISION_ORDER,
        "max_field_size": int(max_field_size),
        "min_year": int(years[0]) if years else None,
        "max_year": int(years[-1]) if years else None,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    return {"bands": bands, "metadata": metadata}


def write_outputs(payload: dict, outputs: Iterable[Path]) -> None:
    for path in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default="data/processed/all_placements.csv",
        type=Path,
        help="Path to the consolidated placements CSV",
    )
    parser.add_argument(
        "--output",
        action="append",
        dest="outputs",
        type=Path,
        help="Destination for the JSON payload (can be supplied multiple times)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    outputs: List[Path]
    if args.outputs:
        outputs = args.outputs
    else:
        outputs = [Path("apps/band-positions/public/data/band_positions.json")]

    df = load_dataset(args.input)
    payload = build_payload(df)
    write_outputs(payload, outputs)


if __name__ == "__main__":
    main()
