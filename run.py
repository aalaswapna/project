from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List

import pandas as pd
import torch

from database.mongo import MongoGateway
from database.nutrition_ingest import NutritionIngestor
from evaluation.evaluator import Evaluator
from fusion.multimodal_model import MultimodalFusionModel
from scripts.kaggle_pipeline import KagglePipeline
from training.data_pipeline import ImagePreprocessor
from training.datasets import class_weights_from_train_df, make_dataloaders
from training.trainer import Trainer
from utils.config import ensure_directories, load_yaml, save_json, set_global_seed, timestamp_tag
from utils.gpu import gpu_snapshot, require_gpu
from utils.logger import setup_logger


def verify_kaggle_json(path: str | Path) -> Path:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError("kaggle.json not found in project root")
    return p


def abort_with_manifest_failures(failures) -> None:
    lines = ["Dataset manifest check failed for:"]
    for fail in failures:
        reason_text = "; ".join(fail.reasons)
        lines.append(f"- {fail.dataset} [{fail.dataset_kind}] -> {reason_text}")
    msg = "\n".join(lines)
    raise RuntimeError(msg)


def log_manifest_failures(logger, failures) -> None:
    if not failures:
        return
    logger.warning("Some dataset manifests failed checks and will be skipped: %s", len(failures))
    for fail in failures:
        reason_text = "; ".join(fail.reasons[:3])
        if len(fail.reasons) > 3:
            reason_text += f"; ... (+{len(fail.reasons) - 3} more)"
        logger.warning("Skipping %s [%s]: %s", fail.dataset, fail.dataset_kind, reason_text)


def load_passed_from_manifest(report_path: str | Path) -> tuple[List[str], List[str], Dict[str, List[str]]]:
    p = Path(report_path)
    if not p.exists():
        raise FileNotFoundError(f"Manifest report not found: {p}")

    payload = json.loads(p.read_text(encoding="utf-8"))
    image_rows = payload.get("image", [])
    nutrition_rows = payload.get("nutrition", [])

    passed_images = [row["dataset"] for row in image_rows if bool(row.get("passed"))]
    passed_nutrition = [row["dataset"] for row in nutrition_rows if bool(row.get("passed"))]

    failed = {
        "image": [row["dataset"] for row in image_rows if not bool(row.get("passed"))],
        "nutrition": [row["dataset"] for row in nutrition_rows if not bool(row.get("passed"))],
    }
    return passed_images, passed_nutrition, failed


def launch_backend(cfg: Dict, checkpoint_path: Path) -> subprocess.Popen:
    host = cfg["backend"]["host"]
    port = str(cfg["backend"]["port"])

    env = os.environ.copy()
    env["MODEL_CHECKPOINT"] = str(checkpoint_path.resolve())

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "api.main:app",
        "--host",
        host,
        "--port",
        port,
    ]
    return subprocess.Popen(cmd, env=env)


def _npm_executable() -> str:
    if shutil.which("npm"):
        return "npm"
    if shutil.which("npm.cmd"):
        return "npm.cmd"
    raise FileNotFoundError("npm is not installed or not in PATH")


def launch_frontend(cfg: Dict) -> subprocess.Popen:
    npm = _npm_executable()
    frontend_dir = Path("frontend")

    if not (frontend_dir / "node_modules").exists():
        subprocess.run([npm, "install"], cwd=frontend_dir, check=True)

    host = cfg["frontend"]["host"]
    port = str(cfg["frontend"]["port"])
    cmd = [npm, "run", "dev", "--", "--host", host, "--port", port]
    return subprocess.Popen(cmd, cwd=frontend_dir)


def main() -> int:
    cfg = load_yaml("configs/default.yaml")
    cfg["datasets"]["min_usable_images"] = int(os.environ.get("MIN_USABLE_IMAGES", "200"))
    ensure_directories(cfg)
    set_global_seed(int(cfg["project"]["random_seed"]))

    run_id = timestamp_tag()
    run_log = Path(cfg["paths"]["logs_dir"]) / f"run_{run_id}.log"
    logger = setup_logger("run", run_log)

    logger.info("Run started: %s", run_id)
    logger.info("Minimum usable image threshold: %s", cfg["datasets"]["min_usable_images"])
    logger.info("Strict manifest mode: %s", os.environ.get("STRICT_MANIFEST", "0").strip() == "1")

    kaggle_json = verify_kaggle_json("kaggle.json")
    require_gpu()
    logger.info("GPU verified: %s", gpu_snapshot())

    kaggle_pipeline = KagglePipeline(cfg, logger)
    kaggle_pipeline.authenticate(kaggle_json)

    resume_from_manifest = os.environ.get("RESUME_FROM_MANIFEST", "0").strip() == "1"
    if resume_from_manifest:
        manifest_path = Path(cfg["paths"]["dataset_reports_dir"]) / "manifest_report.json"
        approved_image_datasets, approved_nutrition_datasets, failed_sets = load_passed_from_manifest(manifest_path)
        logger.info("Resuming from existing manifest report: %s", manifest_path)
        logger.info("Using passed image datasets only: %s", approved_image_datasets)
        logger.info("Using passed nutrition datasets only: %s", approved_nutrition_datasets)
        logger.info("Skipping failed image datasets: %s", failed_sets["image"])
        logger.info("Skipping failed nutrition datasets: %s", failed_sets["nutrition"])
    else:
        image_results, nutrition_results = kaggle_pipeline.inspect_all_manifests()
        failures = [r for r in (image_results + nutrition_results) if not r.passed]
        approved_image_datasets = [r.dataset for r in image_results if r.passed]
        approved_nutrition_datasets = [r.dataset for r in nutrition_results if r.passed]
        if failures:
            strict_manifest = os.environ.get("STRICT_MANIFEST", "0").strip() == "1"
            if strict_manifest:
                abort_with_manifest_failures(failures)
            log_manifest_failures(logger, failures)
            logger.info("Continuing with passed image datasets: %s", approved_image_datasets)
            logger.info("Continuing with passed nutrition datasets: %s", approved_nutrition_datasets)

    if not approved_image_datasets:
        raise RuntimeError("No approved image datasets available to continue.")
    if not approved_nutrition_datasets:
        raise RuntimeError("No approved nutrition datasets available to continue.")

    extracted_images = kaggle_pipeline.download_approved_datasets(approved_image_datasets, output_subdir="images")
    extracted_nutrition = kaggle_pipeline.download_approved_datasets(approved_nutrition_datasets, output_subdir="nutrition")

    mongo = MongoGateway(cfg, logger=logger)
    ingestor = NutritionIngestor(cfg, logger, mongo)
    nutrition_summary = ingestor.ingest(extracted_nutrition)
    save_json(Path(cfg["paths"]["logs_dir"]) / f"nutrition_ingest_{run_id}.json", nutrition_summary)

    preprocessor = ImagePreprocessor(cfg, logger)
    try:
        data_summary = preprocessor.build_processed_dataset(extracted_images)
    except RuntimeError as ex:
        err = str(ex)
        if "below required minimum" in err:
            logger.warning("Initial image count below threshold. Attempting additional manifest-verified vitamin datasets.")
            discovery_queries = [
                "vitamin deficiency",
                "nutritional deficiency",
                "iron deficiency",
                "vitamin dataset",
            ]
            reject_keywords = [
                "cancer",
                "tumor",
                "melanoma",
                "fracture",
                "covid",
                "xray",
                "pneumonia",
            ]
            extras = kaggle_pipeline.discover_additional_image_datasets(
                existing_refs=approved_image_datasets,
                queries=discovery_queries,
                reject_keywords=reject_keywords,
                max_candidates=80,
                max_use=12,
            )
            if extras:
                logger.info("Downloading additional datasets: %s", extras)
                extra_extracted = kaggle_pipeline.download_approved_datasets(extras, output_subdir="images_extra")
                extracted_images.update(extra_extracted)
                data_summary = preprocessor.build_processed_dataset(extracted_images)
            else:
                logger.error("No additional manifest-verified datasets discovered.")
                raise
        else:
            raise
    if int(data_summary.total_images) < 500:
        logger.warning(
            "Dataset meets absolute minimum (>=200) but below recommended size (500). Current usable images: %s",
            data_summary.total_images,
        )

    train_ds, val_ds, test_ds, train_loader, val_loader, test_loader = make_dataloaders(
        cfg,
        data_summary.train_csv,
        data_summary.val_csv,
        data_summary.test_csv,
    )

    train_df = pd.read_csv(data_summary.train_csv)
    class_weights = class_weights_from_train_df(train_df)

    model = MultimodalFusionModel(
        backbone_name=cfg["training"]["backbone"],
        num_classes=len(data_summary.class_to_idx),
        q_dim=9,
        freeze_ratio=float(cfg["training"]["freeze_ratio"]),
    )

    model_run_dir = Path(cfg["paths"]["models_dir"]) / run_id
    eval_run_dir = Path(cfg["paths"]["evaluation_dir"]) / run_id

    trainer = Trainer(
        cfg=cfg,
        logger=logger,
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        class_weights=class_weights,
        class_names=[data_summary.idx_to_class[i] for i in sorted(data_summary.idx_to_class)],
        output_dir=model_run_dir,
    )
    train_artifacts = trainer.train()

    evaluator = Evaluator(
        cfg=cfg,
        logger=logger,
        model=model,
        checkpoint_path=train_artifacts.best_checkpoint,
        test_loader=test_loader,
        class_names=[data_summary.idx_to_class[i] for i in sorted(data_summary.idx_to_class)],
        output_dir=eval_run_dir,
    )
    eval_artifacts = evaluator.evaluate()

    latest_dir = Path(cfg["paths"]["models_dir"]) / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)
    latest_checkpoint = latest_dir / "best_model.pt"
    shutil.copy2(train_artifacts.best_checkpoint, latest_checkpoint)

    meta_payload = {
        "run_id": run_id,
        "checkpoint": str(train_artifacts.best_checkpoint),
        "latest_checkpoint": str(latest_checkpoint),
        "data_report": str(data_summary.report_path),
        "evaluation_metrics": str(eval_artifacts.metrics_json),
        "nutrition_summary": nutrition_summary,
    }
    save_json(model_run_dir / "run_metadata.json", meta_payload)

    backend_proc = launch_backend(cfg, latest_checkpoint)
    time.sleep(3)
    frontend_proc = launch_frontend(cfg)

    backend_url = f"http://{cfg['backend']['host']}:{cfg['backend']['port']}"
    frontend_url = f"http://{cfg['frontend']['host']}:{cfg['frontend']['port']}"

    print("\nExecution complete. Services started:")
    print(f"Backend API: {backend_url}")
    print(f"Frontend UI: {frontend_url}")
    print(f"Run ID: {run_id}")
    print(f"Best checkpoint: {train_artifacts.best_checkpoint}")
    print(f"Evaluation metrics: {eval_artifacts.metrics_json}")

    def shutdown(*_):
        for proc in [frontend_proc, backend_proc]:
            if proc and proc.poll() is None:
                proc.terminate()
        time.sleep(1)
        for proc in [frontend_proc, backend_proc]:
            if proc and proc.poll() is None:
                proc.kill()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    if os.environ.get("DETACH_SERVICES", "0").strip() == "1":
        logger.info("DETACH_SERVICES=1 set; leaving backend/frontend running and exiting orchestrator.")
        return 0

    while True:
        if backend_proc.poll() is not None:
            raise RuntimeError("Backend process exited unexpectedly")
        if frontend_proc.poll() is not None:
            raise RuntimeError("Frontend process exited unexpectedly")
        time.sleep(2)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as ex:
        print(f"PIPELINE FAILED: {ex}")
        raise
