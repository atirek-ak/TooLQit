#!/usr/bin/env python3

from pathlib import Path
import csv
import argparse
import re


TAU_TAGS = {
    "HHbT",
    "HHbV",
    "LHbT",
    "LHbV",
}


TAG_FILES = {
    "HH_bTag": "HHbT",
    "HH_bVeto": "HHbV",
    "LH_bTag": "LHbT",
    "LH_bVeto": "LHbV",
}


def coupling_name(model: str, lepton: str, quark: str, chirality: str) -> str:
    if model.startswith(("S", "R")):
        prefix = "Y"
    elif model.startswith(("U", "V")):
        prefix = "X"
    else:
        raise ValueError(f"Cannot determine scalar/vector type for model {model}")

    return f"{prefix}{lepton}{quark}{chirality}{lepton}x{quark}"


def read_efficiency_file(path: Path) -> tuple[str, list[list[str]]]:
    """
    Read the bin, event count, and efficiency rows from a tag table.
    """
    rows = []
    bin_name = None
    with path.open(encoding="utf-8") as f:
        for line in f:
            columns = line.split()
            if not columns:
                continue

            if columns[0].startswith("bin_") and len(columns) >= 3:
                bin_name = columns[0]
                continue

            if len(columns) < 3:
                continue

            try:
                float(columns[0])
                float(columns[1])
                float(columns[2])
            except ValueError:
                continue

            if bin_name is None:
                bin_name = "Bin"
            rows.append(columns[:3])

    if not rows:
        raise ValueError(f"No efficiency rows found in {path}")

    return bin_name, rows


def collect_efficiencies(input_dir: Path, output_dir: Path):
    """
    Expected input structure:

        input_dir/
            <model>/<coupling_mode>/<NP|NPQED>/<process>/Events/<mass>/
                <mass>_<HH|LH>_b<Tag|Veto>.dat

    Produces:

        output_dir/
            <model>/efficiency/<i|t>/<coupling>/<mass>/<tag>.csv
    """

    if output_dir.name == "data_new":
        output_dir = output_dir / "model"

    output_dir.mkdir(parents=True, exist_ok=True)

    data = {}

    input_paths = sorted(
        path
        for pattern in ("*_bTag.dat", "*_bVeto.dat", "*electron.dat", "*muon.dat")
        for path in input_dir.rglob(pattern)
    )
    for path in input_paths:
        tau_match = re.fullmatch(r"(\d+)_(HH|LH)_(bTag|bVeto)", path.stem)
        lepton_match = re.fullmatch(r"(\d+)(electron|muon)", path.stem)
        if tau_match:
            mass_text, lepton_pair, tag_type = tau_match.groups()
            tag = TAG_FILES[f"{lepton_pair}_{tag_type}"]
        elif lepton_match:
            mass_text, _lepton_flavor = lepton_match.groups()
            tag = None
        else:
            continue

        event_dir = path.parent
        events_dir = event_dir.parent
        run_dir = events_dir.parent
        channel_dir = run_dir.parent
        mode_dir = channel_dir.parent
        model_dir = mode_dir.parent
        if events_dir.name != "Events" or channel_dir.name not in {"NP", "NPQED"}:
            continue

        model = model_dir.name
        channel = "i" if channel_dir.name == "NP" else "t"
        encoded_couplings = run_dir.name.removeprefix(f"{channel_dir.name}_").split("_")
        first_coupling = re.fullmatch(
            r"LM(\d)(\d)(LL|LR|RL|RR)", encoded_couplings[0]
        )
        if first_coupling is None:
            continue
        coupling_tokens = [first_coupling.groups()]
        chirality = first_coupling.group(3)
        for encoded in encoded_couplings[1:]:
            token_match = re.fullmatch(
                r"(?:LM)?(\d)(\d)(LL|LR|RL|RR)?", encoded
            )
            if token_match is None:
                coupling_tokens = []
                break
            lepton, quark, next_chirality = token_match.groups()
            chirality = next_chirality or chirality
            coupling_tokens.append((lepton, quark, chirality))
        if not coupling_tokens:
            continue

        coupling = "_".join(
            coupling_name(model, lepton, quark, token_chirality)
            for lepton, quark, token_chirality in coupling_tokens
        )
        try:
            bin_name, rows = read_efficiency_file(path)
        except ValueError as exc:
            print(f"Skipping {path}: {exc}")
            continue

        try:
            mass = int(mass_text)
        except ValueError:
            continue

        output_path = output_dir / model / "efficiency" / channel / coupling / str(mass)
        if tag is None:
            output_path = output_path.with_suffix(".csv")
        else:
            output_path = output_path / f"{tag}.csv"
        data[output_path] = (bin_name, rows)

    for output_path, (bin_name, rows) in data.items():
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([bin_name, "nEvents", "Efficiencies"])
            writer.writerows(rows)
        print(f"Wrote {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "input_dir",
        type=Path,
    )

    parser.add_argument(
        "output_dir",
        type=Path,
        help="Output root; data_new automatically writes under <root>/model",
    )

    args = parser.parse_args()

    collect_efficiencies(
        args.input_dir,
        args.output_dir,
    )