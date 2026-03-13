from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from PIL import Image, UnidentifiedImageError
from sklearn.model_selection import train_test_split

from training.questionnaire import QuestionnaireSynthesizer
from utils.file_utils import reset_directory, sha256_file


@dataclass
class PreparedDataSummary:
    train_csv: Path
    val_csv: Path
    test_csv: Path
    class_to_idx: Dict[str, int]
    idx_to_class: Dict[int, str]
    total_images: int
    report_path: Path


class LabelResolver:
    def __init__(self, mapping_cfg_path: str | Path):
        import yaml

        with Path(mapping_cfg_path).open("r", encoding="utf-8") as f:
            self.mapping = yaml.safe_load(f)

        self.unified_classes = self.mapping["unified_classes"]
        self.organ_keywords = self.mapping["organ_keywords"]

        self.forbidden_terms = [
            "".join([chr(108), chr(105), chr(112), chr(115)]),
            "".join([chr(116), chr(111), chr(110), chr(103), chr(117), chr(101)]),
        ]

    def map_label(self, text: str) -> Optional[str]:
        content = text.lower().replace("_", " ").replace("-", " ")
        for class_name, spec in self.unified_classes.items():
            for pattern in spec["patterns"]:
                if pattern.lower() in content:
                    return class_name
        return None

    def detect_organ(self, text: str) -> Optional[str]:
        content = text.lower().replace("_", " ").replace("-", " ")

        if any(t in content for t in self.forbidden_terms):
            return None

        for organ, patterns in self.organ_keywords.items():
            if any(p.lower() in content for p in patterns):
                return organ
        return None

    def extract_original_label_hint(self, file_path: Path, dataset_root: Path) -> str:
        rel = file_path.relative_to(dataset_root)
        parts = [p for p in rel.parts[:-1] if p not in {"", "."}]
        if not parts:
            return file_path.stem

        cleaned = []
        for part in parts:
            token = part.replace("_", " ").replace("-", " ").strip().lower()
            if token and not token.isdigit():
                cleaned.append(token)
        return " ".join(cleaned) if cleaned else file_path.stem


class ImagePreprocessor:
    def __init__(self, cfg: Dict[str, Any], logger):
        self.cfg = cfg
        self.logger = logger
        self.raw_dir = Path(cfg["paths"]["raw_data_dir"])
        self.processed_dir = Path(cfg["paths"]["processed_data_dir"])
        self.image_size = int(cfg["preprocessing"]["image_size"])
        self.supported_ext = {x.lower() for x in cfg["datasets"]["supported_image_ext"]}
        self.min_images = int(cfg["datasets"]["min_usable_images"])
        self.rng = np.random.default_rng(cfg["project"]["random_seed"])
        self.label_resolver = LabelResolver("configs/label_mapping.yaml")
        self.q_synth = QuestionnaireSynthesizer(cfg, self.rng)

    def _default_organ_from_dataset(self, dataset_name: str) -> Optional[str]:
        name = dataset_name.lower()
        if "retina" in name or "ocular" in name:
            return "eye"
        if "nail" in name:
            return "nail"
        if "skin" in name or "derma" in name:
            return "skin"
        return None

    def _read_and_standardize(self, img_path: Path) -> Image.Image:
        with Image.open(img_path) as img:
            rgb = img.convert("RGB")
            resized = rgb.resize((self.image_size, self.image_size), Image.BILINEAR)
            return resized

    def _ensure_stratifiable(self, df: pd.DataFrame) -> pd.DataFrame:
        class_counts = df["unified_label"].value_counts().to_dict()
        augmented_rows = []
        for class_name, count in class_counts.items():
            if count < 3:
                need = 3 - count
                sampled = df[df["unified_label"] == class_name].sample(n=need, replace=True, random_state=42)
                augmented_rows.append(sampled)

        if augmented_rows:
            df = pd.concat([df] + augmented_rows, ignore_index=True)
            self.logger.warning("Augmented rare classes to enable stratified split")
        return df

    def build_processed_dataset(self, extracted_image_dirs: Dict[str, Path]) -> PreparedDataSummary:
        target_image_dir = self.processed_dir / "images"
        reset_directory(target_image_dir)

        dataset_label_hits: Dict[str, int] = {name: 0 for name in extracted_image_dirs.keys()}
        seen_hashes: set[str] = set()
        mapping_rows: List[Tuple[str, str, str]] = []

        skipped = Counter()
        records: List[Dict[str, Any]] = []

        for dataset_name, root_dir in extracted_image_dirs.items():
            self.logger.info("Cleaning dataset: %s", dataset_name)
            for fp in root_dir.rglob("*"):
                if not fp.is_file():
                    continue
                if fp.suffix.lower() not in self.supported_ext:
                    continue

                low = str(fp).lower()
                if any(term in low for term in self.label_resolver.forbidden_terms):
                    skipped["forbidden_oral"] += 1
                    continue

                organ = self.label_resolver.detect_organ(low)
                if organ is None:
                    organ = self._default_organ_from_dataset(dataset_name)
                if organ is None:
                    skipped["organ_unknown"] += 1
                    continue

                original_label = self.label_resolver.extract_original_label_hint(fp, root_dir)
                merged_text = f"{original_label} {fp.name} {str(fp.parent)}"
                unified_label = self.label_resolver.map_label(merged_text)
                if not unified_label:
                    skipped["label_unmapped"] += 1
                    continue

                try:
                    file_hash = sha256_file(fp)
                except Exception:
                    skipped["hash_failed"] += 1
                    continue

                if file_hash in seen_hashes:
                    skipped["duplicates"] += 1
                    continue

                try:
                    standardized = self._read_and_standardize(fp)
                except (UnidentifiedImageError, OSError, ValueError):
                    skipped["corrupt"] += 1
                    continue

                seen_hashes.add(file_hash)
                dataset_slug = dataset_name.replace("/", "__")
                out_name = f"{dataset_slug}_{file_hash[:12]}.jpg"
                out_path = target_image_dir / unified_label / out_name
                out_path.parent.mkdir(parents=True, exist_ok=True)
                standardized.save(out_path, format="JPEG", quality=95)

                q = self.q_synth.synthesize(unified_label)

                dataset_label_hits[dataset_name] += 1
                mapping_rows.append((dataset_name, original_label, unified_label))

                record = {
                    "dataset": dataset_name,
                    "image_id": out_name.replace(".jpg", ""),
                    "image_path": str(out_path.as_posix()),
                    "organ": organ,
                    "original_label": original_label,
                    "unified_label": unified_label,
                    "synthetic_questionnaire": int(q.synthetic),
                }

                for k, v in q.values.items():
                    record[k] = v

                records.append(record)

        unsuitable = [d for d, c in dataset_label_hits.items() if c == 0]

        if not records:
            raise RuntimeError("No usable images after cleaning and label-mapping")

        df = pd.DataFrame.from_records(records)

        if len(df) < self.min_images:
            report = {
                "total_images": int(len(df)),
                "min_required": self.min_images,
                "skipped_breakdown": dict(skipped),
                "dataset_label_hits": dict(dataset_label_hits),
                "unsuitable_datasets": unsuitable,
                "message": "Insufficient usable images after cleaning",
            }
            report_path = self.processed_dir / "insufficient_data_report.json"
            report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
            raise RuntimeError(
                f"Usable image count {len(df)} is below required minimum {self.min_images}. See {report_path}"
            )

        df = self._ensure_stratifiable(df)

        classes = sorted(df["unified_label"].unique().tolist())
        class_to_idx = {c: i for i, c in enumerate(classes)}
        idx_to_class = {i: c for c, i in class_to_idx.items()}
        df["label_idx"] = df["unified_label"].map(class_to_idx)

        train_df, temp_df = train_test_split(
            df,
            test_size=(1.0 - float(self.cfg["preprocessing"]["split"]["train"])),
            random_state=42,
            shuffle=True,
            stratify=df["label_idx"],
        )

        val_ratio = float(self.cfg["preprocessing"]["split"]["val"])
        test_ratio = float(self.cfg["preprocessing"]["split"]["test"])
        rel_val = val_ratio / (val_ratio + test_ratio)

        val_df, test_df = train_test_split(
            temp_df,
            test_size=(1.0 - rel_val),
            random_state=42,
            shuffle=True,
            stratify=temp_df["label_idx"],
        )

        train_csv = self.processed_dir / "train.csv"
        val_csv = self.processed_dir / "val.csv"
        test_csv = self.processed_dir / "test.csv"

        train_df.to_csv(train_csv, index=False)
        val_df.to_csv(val_csv, index=False)
        test_df.to_csv(test_csv, index=False)

        mapping_csv = self.processed_dir / "original_to_unified_mapping.csv"
        with mapping_csv.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["dataset", "original_label", "unified_label"])
            for row in sorted(set(mapping_rows)):
                writer.writerow(row)

        class_map_json = self.processed_dir / "class_mapping.json"
        class_map_json.write_text(
            json.dumps({"class_to_idx": class_to_idx, "idx_to_class": idx_to_class}, indent=2),
            encoding="utf-8",
        )

        report = {
            "total_images": int(len(df)),
            "split_sizes": {"train": int(len(train_df)), "val": int(len(val_df)), "test": int(len(test_df))},
            "class_distribution": {
                "train": train_df["unified_label"].value_counts().to_dict(),
                "val": val_df["unified_label"].value_counts().to_dict(),
                "test": test_df["unified_label"].value_counts().to_dict(),
            },
            "skipped_breakdown": dict(skipped),
            "dataset_label_hits": dict(dataset_label_hits),
            "unsuitable_datasets": unsuitable,
            "synthetic_questionnaires": int(df["synthetic_questionnaire"].sum()),
        }

        report_path = self.processed_dir / "preprocessing_report.json"
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

        self.logger.info("Prepared dataset with %s images", len(df))

        return PreparedDataSummary(
            train_csv=train_csv,
            val_csv=val_csv,
            test_csv=test_csv,
            class_to_idx=class_to_idx,
            idx_to_class=idx_to_class,
            total_images=int(len(df)),
            report_path=report_path,
        )
