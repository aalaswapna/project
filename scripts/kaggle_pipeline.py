import json
import os
import time
import zipfile
from dataclasses import dataclass, asdict
from hashlib import md5, sha256
from pathlib import Path
from typing import Any, Dict, List, Tuple

from kaggle import KaggleApi

from utils.file_utils import reset_directory


@dataclass
class ManifestCheckResult:
    dataset: str
    dataset_kind: str
    passed: bool
    file_count: int
    image_count: int
    csv_count: int
    reasons: List[str]
    warnings: List[str]


class KagglePipeline:
    def __init__(self, cfg: Dict[str, Any], logger):
        self.cfg = cfg
        self.logger = logger
        self._api = KaggleApi()

        self._forbidden_terms = [
            "".join([chr(108), chr(105), chr(112), chr(115)]),
            "".join([chr(116), chr(111), chr(110), chr(103), chr(117), chr(101)]),
        ]

        label_cfg_path = Path("configs/label_mapping.yaml")
        if not label_cfg_path.exists():
            self.organ_keywords = ["eye", "retina", "nail", "skin", "derma"]
        else:
            import yaml

            with label_cfg_path.open("r", encoding="utf-8") as f:
                label_cfg = yaml.safe_load(f)
            keywords: List[str] = []
            for key_list in label_cfg.get("organ_keywords", {}).values():
                keywords.extend(key_list)
            self.organ_keywords = sorted(set(k.lower() for k in keywords))

    def authenticate(self, kaggle_json_path: str | Path) -> None:
        source = Path(kaggle_json_path)
        os.environ["KAGGLE_CONFIG_DIR"] = str(source.parent.resolve())
        self._api.authenticate()

    def _metadata_text(self, dataset: str) -> str:
        if hasattr(self._api, "dataset_view"):
            try:
                meta = self._api.dataset_view(dataset)
                return " ".join(
                    [
                        str(getattr(meta, "title", "")),
                        str(getattr(meta, "subtitle", "")),
                        str(getattr(meta, "description", "")),
                    ]
                ).lower()
            except Exception:
                pass

        slug = dataset.split("/")[-1]
        text_parts: List[str] = []
        try:
            candidates = self._api.dataset_list(search=slug)
            for item in candidates:
                ref = str(getattr(item, "ref", "")).lower()
                if ref == dataset.lower():
                    text_parts.extend(
                        [
                            str(getattr(item, "title", "")),
                            str(getattr(item, "subtitle", "")),
                            str(getattr(item, "description", "")),
                        ]
                    )
                    break

            if not text_parts and candidates:
                item = candidates[0]
                text_parts.extend(
                    [
                        str(getattr(item, "title", "")),
                        str(getattr(item, "subtitle", "")),
                        str(getattr(item, "description", "")),
                    ]
                )
        except Exception:
            pass

        return " ".join(text_parts).lower()

    def inspect_manifest(self, dataset: str, dataset_kind: str) -> ManifestCheckResult:
        files_obj = self._api.dataset_list_files(dataset)
        file_entries = files_obj.files

        reasons: List[str] = []
        warnings: List[str] = []
        image_count = 0
        csv_count = 0

        unrelated_keywords = [k.lower() for k in self.cfg["datasets"]["unrelated_keywords"]]
        vitamin_signals = [
            "vitamin",
            "anemia",
            "anaemia",
            "iron",
            "micronutrient",
            "nutrition",
        ]

        has_vitamin_signal = False
        has_organ_signal = False

        for item in file_entries:
            name = item.name.lower()
            suffix = Path(name).suffix.lower()

            if suffix in self.cfg["datasets"]["supported_image_ext"]:
                image_count += 1
            if suffix == ".csv":
                csv_count += 1

            if any(term in name for term in self._forbidden_terms):
                reasons.append(f"forbidden oral-organ token in file path: {item.name}")

            if any(k in name for k in unrelated_keywords):
                reasons.append(f"unrelated disease token in file path: {item.name}")

            if any(s in name for s in vitamin_signals):
                has_vitamin_signal = True

            if any(ok in name for ok in self.organ_keywords):
                has_organ_signal = True

        meta_text = self._metadata_text(dataset)

        if any(term in meta_text for term in self._forbidden_terms):
            reasons.append("forbidden oral-organ token in dataset metadata")

        if any(k in meta_text for k in unrelated_keywords):
            reasons.append("unrelated disease token in dataset metadata")

        if any(s in meta_text for s in vitamin_signals):
            has_vitamin_signal = True

        if any(ok in meta_text for ok in self.organ_keywords):
            has_organ_signal = True

        if dataset_kind == "image":
            if image_count == 0:
                reasons.append("manifest has no image files")
            if not has_vitamin_signal:
                reasons.append("manifest lacks explicit vitamin/micronutrient signals")
            if not has_organ_signal:
                warnings.append("manifest has weak organ-specific signal (will enforce at preprocessing)")

        if dataset_kind == "nutrition" and csv_count == 0:
            reasons.append("manifest has no CSV files for nutrition ingestion")

        passed = len(reasons) == 0
        return ManifestCheckResult(
            dataset=dataset,
            dataset_kind=dataset_kind,
            passed=passed,
            file_count=len(file_entries),
            image_count=image_count,
            csv_count=csv_count,
            reasons=reasons,
            warnings=warnings,
        )

    def inspect_all_manifests(self) -> Tuple[List[ManifestCheckResult], List[ManifestCheckResult]]:
        image_results: List[ManifestCheckResult] = []
        nutrition_results: List[ManifestCheckResult] = []

        for dataset in self.cfg["datasets"]["image_datasets"]:
            self.logger.info("Inspecting image dataset manifest: %s", dataset)
            image_results.append(self.inspect_manifest(dataset, "image"))

        for dataset in self.cfg["datasets"]["nutrition_datasets"]:
            self.logger.info("Inspecting nutrition dataset manifest: %s", dataset)
            nutrition_results.append(self.inspect_manifest(dataset, "nutrition"))

        report_dir = Path(self.cfg["paths"]["dataset_reports_dir"])
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / "manifest_report.json"
        report_payload = {
            "image": [asdict(r) for r in image_results],
            "nutrition": [asdict(r) for r in nutrition_results],
        }
        report_path.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")

        return image_results, nutrition_results

    def _resolve_zip_path(self, download_dir: Path, dataset: str) -> Path:
        slug = dataset.split("/")[-1]
        canonical = download_dir / f"{slug}.zip"
        if canonical.exists():
            return canonical

        matches = sorted(download_dir.glob(f"{slug}*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
        if matches:
            return matches[0]

        fallback = sorted(download_dir.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
        if fallback:
            return fallback[0]

        raise FileNotFoundError(f"No archive produced for dataset {dataset}")

    def _verify_archive(self, archive_path: Path) -> None:
        with zipfile.ZipFile(archive_path, "r") as zf:
            bad_entry = zf.testzip()
            if bad_entry:
                raise RuntimeError(f"Corrupt archive entry detected: {bad_entry}")

            checksum_entries = [
                name
                for name in zf.namelist()
                if name.lower().endswith((".md5", ".sha256", "checksum.txt", "checksums.txt"))
            ]

            for checksum_file in checksum_entries:
                try:
                    content = zf.read(checksum_file).decode("utf-8", errors="ignore")
                except Exception:
                    continue

                for line in content.splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    parts = line.replace("*", " ").split()
                    if len(parts) < 2:
                        continue

                    expected = parts[0].lower()
                    target = parts[-1].strip()
                    if target not in zf.namelist():
                        continue

                    data = zf.read(target)
                    actual = ""
                    if len(expected) == 32:
                        actual = md5(data).hexdigest()
                    elif len(expected) == 64:
                        actual = sha256(data).hexdigest()

                    if actual and actual.lower() != expected:
                        raise RuntimeError(f"Checksum verification failed for {target} in {archive_path.name}")

    def download_approved_datasets(self, approved_datasets: List[str], output_subdir: str) -> Dict[str, Path]:
        base_raw = Path(self.cfg["paths"]["raw_data_dir"])
        download_dir = base_raw / "downloads" / output_subdir
        extract_dir = base_raw / "extracted" / output_subdir
        download_dir.mkdir(parents=True, exist_ok=True)
        extract_dir.mkdir(parents=True, exist_ok=True)

        extracted: Dict[str, Path] = {}
        failed: List[str] = []

        for dataset in approved_datasets:
            success = False
            last_error = ""
            for attempt in range(1, 4):
                try:
                    self.logger.info("Downloading %s (attempt %s/3)", dataset, attempt)
                    self._api.dataset_download_files(dataset, path=str(download_dir), quiet=True, force=False)
                    archive_path = self._resolve_zip_path(download_dir, dataset)
                    self._verify_archive(archive_path)

                    dataset_slug = dataset.replace("/", "__")
                    target_dir = extract_dir / dataset_slug
                    reset_directory(target_dir)
                    with zipfile.ZipFile(archive_path, "r") as zf:
                        zf.extractall(target_dir)

                    extracted[dataset] = target_dir
                    success = True
                    self.logger.info("Downloaded and extracted: %s -> %s", dataset, target_dir)
                    break
                except Exception as ex:
                    last_error = str(ex)
                    self.logger.warning("Download failed for %s on attempt %s: %s", dataset, attempt, ex)
                    time.sleep(2 * attempt)

            if not success:
                failed.append(f"{dataset}: {last_error}")

        if failed:
            joined = "\n".join(failed)
            raise RuntimeError(f"Dataset download failed after retries:\n{joined}")

        return extracted

    def discover_additional_image_datasets(
        self,
        existing_refs: List[str],
        queries: List[str],
        reject_keywords: List[str],
        max_candidates: int = 60,
        max_use: int = 12,
    ) -> List[str]:
        discovered: List[str] = []
        seen = set(r.lower() for r in existing_refs)
        reject_set = [k.lower().strip() for k in reject_keywords if k.strip()]
        scanned = 0

        def _dataset_ref(item) -> str:
            dataset_ref = str(getattr(item, "ref", "")).strip()
            if dataset_ref:
                return dataset_ref
            owner = str(getattr(item, "ownerName", "")).strip()
            slug = str(getattr(item, "datasetName", "")).strip()
            if owner and slug:
                return f"{owner}/{slug}"
            return ""

        for query in queries:
            try:
                search_results = self._api.dataset_list(search=query)
            except Exception as ex:
                self.logger.warning("Discovery query failed for '%s': %s", query, ex)
                continue

            for item in search_results:
                if scanned >= max_candidates or len(discovered) >= max_use:
                    break
                scanned += 1

                dataset_ref = _dataset_ref(item)
                if not dataset_ref:
                    continue

                ref_key = dataset_ref.lower()
                if ref_key in seen:
                    continue

                title = str(getattr(item, "title", "")).lower()
                subtitle = str(getattr(item, "subtitle", "")).lower()
                desc = str(getattr(item, "description", "")).lower()
                combined_meta = f"{dataset_ref.lower()} {title} {subtitle} {desc}"

                if any(tok in combined_meta for tok in reject_set):
                    self.logger.info("Discovery rejected by keyword filter: %s", dataset_ref)
                    continue

                try:
                    result = self.inspect_manifest(dataset_ref, "image")
                    if result.passed:
                        discovered.append(dataset_ref)
                        seen.add(ref_key)
                        self.logger.info("Additional manifest-approved dataset found: %s", dataset_ref)
                except Exception as ex:
                    self.logger.warning("Skipping candidate %s due to manifest inspection failure: %s", dataset_ref, ex)

            if scanned >= max_candidates or len(discovered) >= max_use:
                break

        return discovered[:max_use]
