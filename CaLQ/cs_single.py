#!/usr/bin/env python3

from pathlib import Path
import csv
import argparse
import re
from typing import Optional


COUPLING_TOKEN = re.compile(r"LM(\d)(\d)(LL|LR|RL|RR)")


def coupling_name(token: str, model: str) -> str:
    match = COUPLING_TOKEN.fullmatch(token)
    if match is None:
        raise ValueError(f"Unsupported coupling token: {token}")

    if model.startswith(("S", "R")):
        prefix = "Y"
    elif model.startswith(("U", "V")):
        prefix = "X"
    else:
        raise ValueError(f"Cannot determine scalar/vector type for model {model}")

    first, second, chirality = match.groups()
    return f"{prefix}{first}{second}{chirality}{first}x{second}"


def read_summary(path: Path) -> dict[float, float]:
    mass_index = None
    cross_section_index = None
    mass_to_value = {}

    with path.open(encoding="utf-8") as f:
        for line in f:
            columns = line.lstrip("#").split()
            if "run_name" in columns and "cross" in columns:
                mass_index = columns.index("run_name")
                cross_section_index = columns.index("cross")
                continue

            if mass_index is None or len(columns) <= max(
                mass_index, cross_section_index
            ):
                continue

            try:
                mass = float(columns[mass_index])
                cross_section = float(columns[cross_section_index])
            except ValueError:
                continue

            mass_to_value[mass] = cross_section

    return mass_to_value


def parse_coupling_tokens(encoded: str) -> Optional[list[str]]:
    parts = encoded.split("_")
    first_match = COUPLING_TOKEN.fullmatch(parts[0])
    if first_match is None:
        return None

    tokens = [parts[0]]
    chirality = first_match.group(3)
    for part in parts[1:]:
        match = re.fullmatch(r"(?:LM)?(\d)(\d)(LL|LR|RL|RR)?", part)
        if match is None:
            return None
        first, second, next_chirality = match.groups()
        chirality = next_chirality or chirality
        tokens.append(f"LM{first}{second}{chirality}")

    return tokens


def collect_cross_sections(input_dir: Path, output_dir: Path):
    """Aggregate NP and NPQED summaries into model cross-section tables."""
    if output_dir.name == "data_new":
        output_dir = output_dir / "model"

    tables = {}

    for path in sorted(input_dir.rglob("*_out.txt")):
        relative_parts = path.relative_to(input_dir).parts
        stem = path.stem.removesuffix("_out")
        channel = next(
            (part for part in relative_parts if part in {"NP", "NPQED"}),
            None,
        )
        if channel is None:
            channel = next(
                (candidate for candidate in ("NPQED", "NP") if stem.startswith(f"{candidate}_")),
                None,
            )
        if channel is None:
            continue

        channel_index = relative_parts.index(channel) if channel in relative_parts else -1
        model = relative_parts[channel_index - 2] if channel_index >= 2 else relative_parts[0]
        prefix = f"{channel}_"
        if not stem.startswith(prefix):
            continue

        tokens = parse_coupling_tokens(stem[len(prefix):])
        if not tokens:
            continue

        column = "_".join(coupling_name(token, model) for token in tokens)
        filename = "tchannel.csv" if channel == "NP" else "interference.csv"
        table = tables.setdefault((model, filename), {})
        mass_values = read_summary(path)
        if mass_values:
            table[column] = mass_values

    for (model, filename), columns in tables.items():
        output_path = output_dir / model / "cross_section" / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        existing_columns = []
        if output_path.is_file():
            with output_path.open(newline="", encoding="utf-8") as f:
                existing_columns = next(csv.reader(f), [])[1:]
        ordered_columns = [column for column in existing_columns if column in columns]
        ordered_columns.extend(sorted(set(columns) - set(ordered_columns)))
        masses = sorted({mass for values in columns.values() for mass in values})

        with output_path.open("w", newline="", encoding="utf-8") as f:
            quoted_headers = [
                '"' + column.replace('"', '""') + '"'
                for column in ordered_columns
            ]
            f.write("Mass," + ",".join(quoted_headers) + "\n")
            writer = csv.writer(f)
            for mass in masses:
                writer.writerow([
                    mass,
                    *(columns[column].get(mass, "") for column in ordered_columns),
                ])

        print(f"Wrote {output_path}")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "input_dir",
        type=Path,
        help="Directory containing cross-section data",
    )

    parser.add_argument(
        "output_dir",
        type=Path,
        help="Output root; data_new automatically writes under <root>/model",
    )

    args = parser.parse_args()

    collect_cross_sections(
        args.input_dir,
        args.output_dir,
    )


if __name__ == "__main__":
    main()