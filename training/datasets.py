from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd
import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from torchvision import transforms


class FusionCsvDataset(Dataset):
    def __init__(self, csv_path: str | Path, transform=None):
        self.df = pd.read_csv(csv_path)
        self.transform = transform
        self.q_cols = [
            "fatigue",
            "diet_type",
            "vegetarian",
            "pregnancy",
            "sunlight_exposure",
            "medications",
            "chronic_illness",
            "allergies",
            "lactose_intolerance",
        ]

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int):
        row = self.df.iloc[idx]
        path = row["image_path"]

        with Image.open(path) as img:
            image = img.convert("RGB")

        if self.transform is not None:
            image = self.transform(image)

        q_vec = torch.tensor([float(row[c]) for c in self.q_cols], dtype=torch.float32)
        label = torch.tensor(int(row["label_idx"]), dtype=torch.long)

        return {
            "image": image,
            "questionnaire": q_vec,
            "label": label,
            "image_id": row.get("image_id", str(idx)),
            "image_path": path,
        }


class TransformFactory:
    @staticmethod
    def build(cfg: Dict[str, Any], backbone: str, is_train: bool):
        norm = cfg["preprocessing"]["normalize"][backbone]
        mean = norm["mean"]
        std = norm["std"]
        size = int(cfg["preprocessing"]["image_size"])

        if is_train:
            return transforms.Compose(
                [
                    transforms.RandomResizedCrop(size=size, scale=(0.88, 1.0), ratio=(0.95, 1.05)),
                    transforms.RandomHorizontalFlip(p=0.5),
                    transforms.RandomRotation(degrees=8),
                    transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.08, hue=0.02),
                    transforms.ToTensor(),
                    transforms.Normalize(mean=mean, std=std),
                ]
            )

        return transforms.Compose(
            [
                transforms.Resize((size, size)),
                transforms.ToTensor(),
                transforms.Normalize(mean=mean, std=std),
            ]
        )


def make_dataloaders(cfg: Dict[str, Any], train_csv: str | Path, val_csv: str | Path, test_csv: str | Path):
    backbone = cfg["training"]["backbone"]

    train_ds = FusionCsvDataset(train_csv, transform=TransformFactory.build(cfg, backbone, is_train=True))
    val_ds = FusionCsvDataset(val_csv, transform=TransformFactory.build(cfg, backbone, is_train=False))
    test_ds = FusionCsvDataset(test_csv, transform=TransformFactory.build(cfg, backbone, is_train=False))

    batch_size = int(cfg["training"]["batch_size"])
    num_workers = int(cfg["training"]["num_workers"])

    sampler = None
    if cfg["training"].get("class_balance_mode", "") == "weighted_sampler":
        labels = train_ds.df["label_idx"].to_numpy()
        class_counts = np.bincount(labels)
        class_weights = 1.0 / np.maximum(class_counts, 1)
        sample_weights = class_weights[labels]
        sampler = WeightedRandomSampler(
            weights=torch.tensor(sample_weights, dtype=torch.double),
            num_samples=len(sample_weights),
            replacement=True,
        )

    train_loader = DataLoader(
        train_ds,
        batch_size=batch_size,
        shuffle=sampler is None,
        sampler=sampler,
        num_workers=num_workers,
        pin_memory=True,
        drop_last=False,
    )

    val_loader = DataLoader(
        val_ds,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True,
        drop_last=False,
    )

    test_loader = DataLoader(
        test_ds,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True,
        drop_last=False,
    )

    return train_ds, val_ds, test_ds, train_loader, val_loader, test_loader


def class_weights_from_train_df(train_df: pd.DataFrame) -> torch.Tensor:
    labels = train_df["label_idx"].astype(int).to_numpy()
    class_counts = np.bincount(labels)
    weights = 1.0 / np.maximum(class_counts, 1)
    weights = weights / weights.sum() * len(weights)
    return torch.tensor(weights, dtype=torch.float32)
