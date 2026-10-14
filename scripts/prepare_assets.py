"""Convert original paper assets for the static project page; leave sources intact."""

import argparse
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from zipfile import ZipFile


def run(*args):
    subprocess.run([str(arg) for arg in args], check=True)


def supplement_rollouts(archive_path, source, destination):
    """Recover recorded samples omitted from the arXiv source package."""
    frames = {}
    final_slots = {"fasterwam": 25, "pi05": 25, "fastwam": 40, "lingbot": 140}
    with ZipFile(archive_path) as archive:
        for policy, final_slot in final_slots.items():
            for seconds in sorted([*range(0, final_slot + 1, 5), 21]):
                name = f"{seconds:03d}s.png"
                relative = Path("appx/real_world_rollouts") / policy / name
                data = archive.read(relative.as_posix())
                original = source / relative
                if original.is_file():
                    if original.read_bytes() != data:
                        raise ValueError(f"Archive does not match the published rollout: {policy}/{name}")
                else:
                    frames[policy, name] = data
    with TemporaryDirectory(prefix="fasterwam-rollouts-") as temp:
        for (policy, name), data in frames.items():
            original = Path(temp) / name
            original.write_bytes(data)
            run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", original, "-quality", "85", destination / policy / f"{original.stem}.webp")
    print(f"Added {len(frames)} original rollout snapshots; shared source frames match exactly.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="arXiv submission directory")
    parser.add_argument("--rollout-archive", type=Path, help="Original project ZIP containing additional recorded rollout snapshots")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    assets = root / "assets"
    (assets / "figures").mkdir(parents=True, exist_ok=True)
    for original, output in [("main_figure", "overview"), ("method_figure", "method")]:
        run("pdftocairo", "-svg", args.source / "figures" / f"{original}.pdf", assets / "figures" / f"{output}.svg")
    run("pdftoppm", "-scale-to", "1200", "-png", "-singlefile", args.source / "figures/main_figure.pdf", assets / "social-preview")
    for policy in ["fasterwam", "pi05", "fastwam", "lingbot"]:
        destination = assets / "rollouts" / policy
        destination.mkdir(parents=True, exist_ok=True)
        for original in sorted((args.source / "appx/real_world_rollouts" / policy).glob("*.png")):
            run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", original, "-quality", "85", destination / f"{original.stem}.webp")
    if args.rollout_archive:
        supplement_rollouts(args.rollout_archive, args.source, assets / "rollouts")
    print("Prepared paper figures, social preview, and rollout snapshots.")


if __name__ == "__main__":
    main()
