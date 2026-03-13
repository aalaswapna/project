from __future__ import annotations

import base64
import io
import json
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import torch
from PIL import Image
from torchvision import transforms

from evaluation.gradcam import GradCAMGenerator
from fusion.multimodal_model import MultimodalFusionModel
from training.questionnaire import encode_questionnaire_payload


class InferenceService:
    def __init__(self, cfg: Dict[str, Any], checkpoint_path: str | Path, logger):
        self.cfg = cfg
        self.logger = logger
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        ckpt = torch.load(checkpoint_path, map_location=self.device)
        self.class_names = ckpt["class_names"]

        self.model = MultimodalFusionModel(
            backbone_name=ckpt["backbone"],
            num_classes=len(self.class_names),
            q_dim=int(ckpt.get("questionnaire_dim", 9)),
            freeze_ratio=0.0,
        )
        self.model.load_state_dict(ckpt["model_state_dict"])
        self.model.to(self.device)
        self.model.eval()

        norm = cfg["preprocessing"]["normalize"][ckpt["backbone"]]
        size = int(cfg["preprocessing"]["image_size"])
        self.transform = transforms.Compose(
            [
                transforms.Resize((size, size)),
                transforms.ToTensor(),
                transforms.Normalize(mean=norm["mean"], std=norm["std"]),
            ]
        )

        self.gradcam = None
        try:
            self.gradcam = GradCAMGenerator(self.model, self.model.gradcam_layer, self.device)
        except Exception as ex:
            self.logger.warning("Grad-CAM unavailable for current checkpoint: %s", ex)

    @staticmethod
    def _severity(confidence: float, questionnaire: Dict[str, Any]) -> float:
        fatigue = float(int(bool(questionnaire.get("fatigue", 0))))
        chronic = float(int(bool(questionnaire.get("chronic_illness", 0))))
        pregnancy = float(int(bool(questionnaire.get("pregnancy", 0))))
        meds = min(1.0, float(questionnaire.get("medications", 0)) / 5.0)
        sunlight = float(questionnaire.get("sunlight_exposure", 2.0))
        sunlight_risk = max(0.0, min(1.0, (2.0 - sunlight) / 2.0))

        burden = (fatigue + chronic + pregnancy + meds + sunlight_risk) / 5.0
        severity = 0.65 * float(confidence) + 0.35 * float(burden)
        return float(max(0.0, min(1.0, severity)))

    @staticmethod
    def _encode_image_to_b64(image_arr: np.ndarray) -> str:
        im = Image.fromarray(image_arr)
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=90)
        return base64.b64encode(buf.getvalue()).decode("ascii")

    def predict(self, pil_images: List[Image.Image], questionnaire_payload: Dict[str, Any]) -> Dict[str, Any]:
        q_vec = torch.tensor(encode_questionnaire_payload(questionnaire_payload, self.cfg), dtype=torch.float32).to(self.device)

        probs_per_image: List[np.ndarray] = []
        heatmaps: List[Dict[str, str]] = []

        with torch.no_grad():
            for pil in pil_images:
                image_tensor = self.transform(pil.convert("RGB"))
                logits, _, _ = self.model(image_tensor.unsqueeze(0).to(self.device), q_vec.unsqueeze(0))
                probs = torch.softmax(logits, dim=1).squeeze(0).detach().cpu().numpy()
                probs_per_image.append(probs)

        avg_probs = np.mean(np.stack(probs_per_image, axis=0), axis=0)
        top_idx = int(np.argmax(avg_probs))
        predicted_class = self.class_names[top_idx]
        confidence = float(avg_probs[top_idx])
        severity = self._severity(confidence, questionnaire_payload)

        if self.gradcam is not None:
            for i, pil in enumerate(pil_images):
                try:
                    img_tensor = self.transform(pil.convert("RGB"))
                    cam = self.gradcam.generate(img_tensor, q_vec, class_idx=top_idx)
                    base = np.array(pil.convert("RGB").resize((cam.shape[1], cam.shape[0])))
                    overlay = GradCAMGenerator.overlay(base, cam)
                    heatmaps.append(
                        {
                            "image_index": i,
                            "base_b64": self._encode_image_to_b64(base),
                            "overlay_b64": self._encode_image_to_b64(overlay),
                        }
                    )
                except Exception as ex:
                    self.logger.warning("Grad-CAM generation failed in inference for image %s: %s", i, ex)

        return {
            "predicted_class": predicted_class,
            "confidence": confidence,
            "severity": severity,
            "probabilities": {self.class_names[i]: float(avg_probs[i]) for i in range(len(self.class_names))},
            "heatmaps": heatmaps,
        }
