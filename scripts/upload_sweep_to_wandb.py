#!/usr/bin/env python
"""
Upload sweep JSON results to WandB after the fact.

Usage:
    uv run python scripts/upload_sweep_to_wandb.py --input-dir experiments/results/sweep
"""

import json
import argparse
from pathlib import Path

import wandb


def main():
    parser = argparse.ArgumentParser(description="Upload sweep results to WandB")
    parser.add_argument("--input-dir", type=str, default="experiments/results/sweep")
    parser.add_argument("--project", type=str, default="sparse_matrix_recovery")
    parser.add_argument("--entity", type=str, default="qsimeon")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    files = sorted(input_dir.glob("*.json"))
    print(f"Found {len(files)} result files")

    for i, f in enumerate(files):
        with open(f) as fh:
            data = json.load(fh)

        config = data["config"]
        distances = data["distances"]

        run = wandb.init(
            project=args.project, entity=args.entity,
            config={**config, "rep": data["rep"], "seed": data["seed"]},
            name=f.stem,
            reinit=True,
        )
        wandb.log(distances)
        wandb.finish()

        if (i + 1) % 100 == 0:
            print(f"  Uploaded {i+1}/{len(files)}")

    print(f"Done! All {len(files)} results uploaded to {args.project}")


if __name__ == "__main__":
    main()
