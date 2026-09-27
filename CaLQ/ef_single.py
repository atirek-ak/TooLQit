#!/usr/bin/env python3

from pathlib import Path
import csv
import argparse


TAU_TAGS = {
    "HHbT",
    "HHbV",
    "LHbT",
    "LHbV",
}


def read_efficiency_file(path: Path) -> float:
    """
    Read the efficiency value from an efficiency file.

    The last whitespace-separated value on a non-comment
    line is treated as the efficiency.
    """

    values = []

    with path.open() as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            try:
                values.append(float(line.split()[-1]))
            except ValueError:
                continue

    if not values:
        raise ValueError(f"No numerical efficiency found in {path}")

    return values[-1]


def collect_efficiencies(input_dir: Path, output_dir: Path):
    """
    Expected structure:

        input_dir/
            <process>/
                <coupling>/
                    <mass>.dat
                    <mass>.txt
                    ...

    Produces:

        output_dir/
            <process>/
                <coupling>.csv

    CSV:

        Mass,Efficiency
        1000,0.12345
        1100,0.23456
        ...
    """

    output_dir.mkdir(parents=True, exist_ok=True)

    data = {}

    for path in input_dir.rglob("*"):
        if not path.is_file():
            continue

        if path.suffix not in {".dat", ".txt"}:
            continue

        # Expected:
        #
        # process / coupling / mass.dat
        #
        # Therefore:
        #   path.parent.parent = process
        #   path.parent         = coupling
        #   path.stem           = mass

        if len(path.parents) < 2:
            continue

        coupling = path.parent.name
        process = path.parent.parent.name

        try:
            mass = int(path.stem)
        except ValueError:
            continue

        try:
            efficiency = read_efficiency_file(path)
        except ValueError as exc:
            print(f"Skipping {path}: {exc}")
            continue

        data.setdefault(process, {})
        data[process].setdefault(coupling, {})
        data[process][coupling][mass] = round(efficiency, 5)

    for process, coupling_data in data.items():

        process_output = output_dir / process
        process_output.mkdir(parents=True, exist_ok=True)

        for coupling, mass_data in coupling_data.items():

            output_path = process_output / f"{coupling}.csv"

            with output_path.open(
                "w",
                newline="",
                encoding="utf-8",
            ) as f:

                writer = csv.writer(f)

                writer.writerow([
                    "Mass",
                    "Efficiency",
                ])

                for mass in sorted(mass_data):
                    writer.writerow([
                        mass,
                        mass_data[mass],
                    ])

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
    )

    args = parser.parse_args()

    collect_efficiencies(
        args.input_dir,
        args.output_dir,
    )