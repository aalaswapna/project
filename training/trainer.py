from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from torch import nn
from torch.cuda.amp import GradScaler, autocast
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR, ReduceLROnPlateau
from tqdm import tqdm

from utils.gpu import gpu_snapshot


@dataclass
class TrainArtifacts:
    best_checkpoint: Path
    history_csv: Path
    history_json: Path


class Trainer:
    def __init__(
        self,
        cfg: Dict[str, Any],
        logger,
        model: nn.Module,
        train_loader,
        val_loader,
        class_weights: torch.Tensor,
        class_names: List[str],
        output_dir: str | Path,
    ):
        self.cfg = cfg
        self.logger = logger
        self.model = model
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.class_names = class_names
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.device = torch.device("cuda")
        self.model.to(self.device)

        loss_name = cfg["training"]["loss"].lower().strip()
        if loss_name != "cross_entropy":
            raise ValueError("This implementation expects single-label cross_entropy")

        self.criterion = nn.CrossEntropyLoss(weight=class_weights.to(self.device))

        self.optimizer = AdamW(
            filter(lambda p: p.requires_grad, self.model.parameters()),
            lr=float(cfg["training"]["optimizer"]["lr"]),
            weight_decay=float(cfg["training"]["optimizer"]["weight_decay"]),
        )

        sched_name = cfg["training"]["scheduler"]["name"].lower().strip()
        if sched_name == "cosine":
            self.scheduler = CosineAnnealingLR(
                self.optimizer,
                T_max=int(cfg["training"]["max_epochs"]),
                eta_min=float(cfg["training"]["scheduler"].get("min_lr", 1e-6)),
            )
            self.scheduler_mode = "step"
        elif sched_name == "plateau":
            self.scheduler = ReduceLROnPlateau(self.optimizer, mode="max", patience=3, factor=0.5)
            self.scheduler_mode = "metric"
        else:
            raise ValueError(f"Unsupported scheduler: {sched_name}")

        self.scaler = GradScaler(enabled=bool(cfg["training"].get("amp", True)))

        self.max_epochs = int(cfg["training"]["max_epochs"])
        self.min_epochs = int(cfg["training"]["min_epochs"])
        self.patience = int(cfg["training"]["early_stopping_patience"])
        self.unfreeze_epoch = int(cfg["training"]["unfreeze_epoch"])
        self.grad_clip_norm = float(cfg["training"].get("grad_clip_norm", 1.0))

    def _run_epoch(self, training: bool) -> Dict[str, float]:
        self.model.train(training)
        loader = self.train_loader if training else self.val_loader

        losses: List[float] = []
        all_preds: List[int] = []
        all_labels: List[int] = []

        desc = "train" if training else "val"
        pbar = tqdm(loader, desc=desc, leave=False)

        for batch in pbar:
            images = batch["image"].to(self.device, non_blocking=True)
            questionnaire = batch["questionnaire"].to(self.device, non_blocking=True)
            labels = batch["label"].to(self.device, non_blocking=True)

            if training:
                self.optimizer.zero_grad(set_to_none=True)

            with torch.set_grad_enabled(training):
                with autocast(enabled=bool(self.cfg["training"].get("amp", True))):
                    logits, _, _ = self.model(images, questionnaire)
                    loss = self.criterion(logits, labels)

                if training:
                    self.scaler.scale(loss).backward()
                    self.scaler.unscale_(self.optimizer)
                    torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.grad_clip_norm)
                    self.scaler.step(self.optimizer)
                    self.scaler.update()

            probs = torch.softmax(logits, dim=1)
            preds = torch.argmax(probs, dim=1)

            losses.append(float(loss.detach().cpu().item()))
            all_preds.extend(preds.detach().cpu().tolist())
            all_labels.extend(labels.detach().cpu().tolist())

        avg_loss = float(np.mean(losses)) if losses else 0.0
        acc = float(accuracy_score(all_labels, all_preds)) if all_preds else 0.0
        p, r, f1, _ = precision_recall_fscore_support(all_labels, all_preds, average="macro", zero_division=0)

        return {
            "loss": avg_loss,
            "acc": float(acc),
            "precision": float(p),
            "recall": float(r),
            "f1": float(f1),
        }

    def train(self) -> TrainArtifacts:
        self.logger.info("GPU Snapshot at training start: %s", gpu_snapshot())

        best_metric = -1.0
        no_improve = 0
        history_rows: List[Dict[str, Any]] = []
        best_checkpoint = self.output_dir / "best_model.pt"

        for epoch in range(1, self.max_epochs + 1):
            if epoch == self.unfreeze_epoch:
                self.logger.info("Unfreezing full image backbone at epoch %s", epoch)
                self.model.unfreeze_backbone()
                self.optimizer = AdamW(
                    filter(lambda p: p.requires_grad, self.model.parameters()),
                    lr=float(self.cfg["training"]["optimizer"]["lr"]) * 0.5,
                    weight_decay=float(self.cfg["training"]["optimizer"]["weight_decay"]),
                )

            train_metrics = self._run_epoch(training=True)
            val_metrics = self._run_epoch(training=False)

            if self.scheduler_mode == "step":
                self.scheduler.step()
            else:
                self.scheduler.step(val_metrics["f1"])

            row = {
                "epoch": epoch,
                "train_loss": train_metrics["loss"],
                "val_loss": val_metrics["loss"],
                "train_acc": train_metrics["acc"],
                "val_acc": val_metrics["acc"],
                "precision": val_metrics["precision"],
                "recall": val_metrics["recall"],
                "f1": val_metrics["f1"],
                "lr": float(self.optimizer.param_groups[0]["lr"]),
            }
            history_rows.append(row)

            self.logger.info(
                "Epoch %s | train_loss=%.4f val_loss=%.4f train_acc=%.4f val_acc=%.4f p=%.4f r=%.4f f1=%.4f lr=%.8f",
                epoch,
                row["train_loss"],
                row["val_loss"],
                row["train_acc"],
                row["val_acc"],
                row["precision"],
                row["recall"],
                row["f1"],
                row["lr"],
            )

            if epoch % 2 == 0:
                self.logger.info("GPU Snapshot epoch %s: %s", epoch, gpu_snapshot())

            metric = val_metrics["f1"]
            if metric > best_metric:
                best_metric = metric
                no_improve = 0
                torch.save(
                    {
                        "epoch": epoch,
                        "model_state_dict": self.model.state_dict(),
                        "optimizer_state_dict": self.optimizer.state_dict(),
                        "best_val_f1": best_metric,
                        "class_names": self.class_names,
                        "backbone": self.cfg["training"]["backbone"],
                        "questionnaire_dim": 9,
                    },
                    best_checkpoint,
                )
                self.logger.info("Saved new best checkpoint at epoch %s (val_f1=%.4f)", epoch, best_metric)
            else:
                no_improve += 1

            if epoch >= self.min_epochs and no_improve >= self.patience:
                self.logger.info("Early stopping triggered at epoch %s", epoch)
                break

        history_df = pd.DataFrame(history_rows)
        history_csv = self.output_dir / "training_history.csv"
        history_json = self.output_dir / "training_history.json"
        history_df.to_csv(history_csv, index=False)
        history_json.write_text(history_df.to_json(orient="records", indent=2), encoding="utf-8")

        summary = {
            "best_val_f1": best_metric,
            "epochs_ran": int(len(history_rows)),
            "checkpoint": str(best_checkpoint),
        }
        (self.output_dir / "training_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

        return TrainArtifacts(best_checkpoint=best_checkpoint, history_csv=history_csv, history_json=history_json)
