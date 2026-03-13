from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import torch
import torch.nn as nn
from torchvision.models import (
    ConvNeXt_Tiny_Weights,
    EfficientNet_B0_Weights,
    ResNet50_Weights,
    ViT_B_16_Weights,
    convnext_tiny,
    efficientnet_b0,
    resnet50,
    vit_b_16,
)


@dataclass
class BackboneBuild:
    model: nn.Module
    feature_dim: int
    gradcam_layer: nn.Module


def freeze_initial_parameters(module: nn.Module, freeze_ratio: float) -> None:
    params = list(module.parameters())
    if not params:
        return
    freeze_count = int(len(params) * freeze_ratio)
    for idx, param in enumerate(params):
        param.requires_grad = idx >= freeze_count


def build_backbone(name: str, freeze_ratio: float = 0.7) -> BackboneBuild:
    name = name.lower().strip()

    if name == "efficientnet_b0":
        model = efficientnet_b0(weights=EfficientNet_B0_Weights.DEFAULT)
        feature_dim = int(model.classifier[1].in_features)
        gradcam_layer = model.features[-1]
        model.classifier = nn.Identity()

    elif name == "resnet50":
        model = resnet50(weights=ResNet50_Weights.DEFAULT)
        feature_dim = int(model.fc.in_features)
        gradcam_layer = model.layer4[-1]
        model.fc = nn.Identity()

    elif name == "convnext_tiny":
        model = convnext_tiny(weights=ConvNeXt_Tiny_Weights.DEFAULT)
        feature_dim = int(model.classifier[2].in_features)
        gradcam_layer = model.features[-1][-1]
        model.classifier = nn.Identity()

    elif name == "vit_b_16":
        model = vit_b_16(weights=ViT_B_16_Weights.DEFAULT)
        feature_dim = int(model.heads.head.in_features)
        gradcam_layer = model.encoder.layers[-1].ln_1
        model.heads = nn.Identity()

    else:
        raise ValueError(f"Unsupported backbone: {name}")

    freeze_initial_parameters(model, freeze_ratio)
    return BackboneBuild(model=model, feature_dim=feature_dim, gradcam_layer=gradcam_layer)


class MultimodalFusionModel(nn.Module):
    def __init__(self, backbone_name: str, num_classes: int, q_dim: int, freeze_ratio: float = 0.7):
        super().__init__()

        build = build_backbone(backbone_name, freeze_ratio=freeze_ratio)
        self.backbone_name = backbone_name
        self.image_encoder = build.model
        self.gradcam_layer = build.gradcam_layer

        self.image_projector = nn.Sequential(
            nn.Linear(build.feature_dim, 256),
            nn.GELU(),
            nn.Dropout(0.2),
        )

        self.questionnaire_encoder = nn.Sequential(
            nn.Linear(q_dim, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU(inplace=True),
        )

        self.fusion_head = nn.Sequential(
            nn.Linear(256 + 64, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.25),
            nn.Linear(256, num_classes),
        )

    def unfreeze_backbone(self) -> None:
        for param in self.image_encoder.parameters():
            param.requires_grad = True

    def forward(self, image: torch.Tensor, questionnaire: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        image_features = self.image_encoder(image)
        if image_features.ndim > 2:
            image_features = torch.flatten(image_features, start_dim=1)

        image_emb = self.image_projector(image_features)
        q_emb = self.questionnaire_encoder(questionnaire)

        fused = torch.cat([image_emb, q_emb], dim=1)
        logits = self.fusion_head(fused)
        return logits, image_emb, q_emb
