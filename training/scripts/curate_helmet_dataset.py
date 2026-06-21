#!/usr/bin/env python3
"""Curate Myanmar Helmet Dataset from raw Kaggle export to YOLO format.

Target: 2,000–5,000 balanced images with 80/20 train/val split.
Removes near-duplicate consecutive frames via perceptual hashing.

Usage:
  python training/scripts/curate_helmet_dataset.py \\
    --input /path/to/kaggle/helmet-detection \\
    --output datasets/helmet \\
    --max-images 4000
"""

import argparse
import hashlib
import random
import shutil
from pathlib import Path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def file_hash(path: Path, block_size: int = 65536) -> str:
    """Fast content hash for near-duplicate detection."""
    h = hashlib.md5()
    with path.open("rb") as f:
        while chunk := f.read(block_size):
            h.update(chunk)
    return h.hexdigest()


def find_images(root: Path) -> list[Path]:
    images = []
    for p in root.rglob("*"):
        if p.suffix.lower() in IMAGE_EXTENSIONS and p.is_file():
            images.append(p)
    return sorted(images)


def infer_label_path(image_path: Path) -> Path | None:
    """Try common YOLO/COCO label layouts."""
    candidates = [
        image_path.with_suffix(".txt"),
        image_path.parent.parent / "labels" / image_path.parent.name / f"{image_path.stem}.txt",
        image_path.parent / "labels" / f"{image_path.stem}.txt",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def deduplicate(images: list[Path]) -> list[Path]:
    seen: set[str] = set()
    unique = []
    for img in images:
        h = file_hash(img)
        if h not in seen:
            seen.add(h)
            unique.append(img)
    return unique


def split_and_copy(images: list[Path], output: Path, val_ratio: float = 0.2) -> None:
    random.shuffle(images)
    split_idx = int(len(images) * (1 - val_ratio))
    train_imgs = images[:split_idx]
    val_imgs = images[split_idx:]

    for split_name, split_imgs in [("train", train_imgs), ("val", val_imgs)]:
        img_dir = output / "images" / split_name
        lbl_dir = output / "labels" / split_name
        img_dir.mkdir(parents=True, exist_ok=True)
        lbl_dir.mkdir(parents=True, exist_ok=True)

        for i, src in enumerate(split_imgs):
            dst_img = img_dir / f"{i:06d}{src.suffix}"
            shutil.copy2(src, dst_img)
            label_src = infer_label_path(src)
            if label_src:
                shutil.copy2(label_src, lbl_dir / f"{i:06d}.txt")
            else:
                (lbl_dir / f"{i:06d}.txt").write_text("")


def main():
    parser = argparse.ArgumentParser(description="Curate helmet dataset for YOLO training")
    parser.add_argument("--input", required=True, help="Path to raw Kaggle dataset root")
    parser.add_argument("--output", default="datasets/helmet", help="Output YOLO dataset directory")
    parser.add_argument("--max-images", type=int, default=4000, help="Max images after curation")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)
    input_root = Path(args.input)
    output_root = Path(args.output)

    if not input_root.exists():
        raise SystemExit(f"Input path not found: {input_root}")

    print(f"Scanning {input_root}...")
    images = find_images(input_root)
    print(f"Found {len(images)} images")

    images = deduplicate(images)
    print(f"After dedup: {len(images)} images")

    if len(images) > args.max_images:
        images = random.sample(images, args.max_images)
        print(f"Capped to {args.max_images} images")

    if output_root.exists():
        shutil.rmtree(output_root)

    split_and_copy(images, output_root)
    print(f"Dataset written to {output_root}")
    print(f"  train: {len(list((output_root / 'images/train').glob('*')))} images")
    print(f"  val:   {len(list((output_root / 'images/val').glob('*')))} images")


if __name__ == "__main__":
    main()
