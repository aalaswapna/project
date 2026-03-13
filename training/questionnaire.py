from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import numpy as np


@dataclass
class QuestionnaireEncoding:
    values: Dict[str, float]
    vector: List[float]
    synthetic: bool


class QuestionnaireSynthesizer:
    def __init__(self, cfg: Dict[str, Any], rng: np.random.Generator):
        self.cfg = cfg
        self.rng = rng
        self.q_cfg = cfg["questionnaire"]
        self.fields = self.q_cfg["fields"]
        self.diet_map = self.q_cfg["diet_type_map"]
        self.profiles = self.q_cfg["synthetic_profiles"]

    def _pick_diet(self, weights: List[float]) -> Tuple[str, int]:
        choices = ["omnivore", "vegetarian", "vegan"]
        idx = int(self.rng.choice(np.arange(len(choices)), p=np.array(weights, dtype=float)))
        return choices[idx], self.diet_map[choices[idx]]

    def synthesize(self, class_name: str) -> QuestionnaireEncoding:
        profile = self.profiles.get(class_name, self.profiles["other_deficiency"])

        diet_label, diet_encoded = self._pick_diet(profile["diet_weights"])

        fatigue = int(self.rng.random() < profile["fatigue_prob"])
        vegetarian = int(diet_label != "omnivore")
        pregnancy = int(self.rng.random() < profile["pregnancy_prob"])
        sunlight_exposure = float(max(0.0, self.rng.normal(loc=profile["sunlight_mean"], scale=0.8)))
        medications = int(min(6, self.rng.poisson(profile["medication_lambda"])))
        chronic_illness = int(self.rng.random() < profile["chronic_prob"])
        allergies = int(self.rng.random() < profile["allergy_prob"])
        lactose_intolerance = int(self.rng.random() < profile["lactose_prob"])

        values = {
            "fatigue": fatigue,
            "diet_type": diet_encoded,
            "vegetarian": vegetarian,
            "pregnancy": pregnancy,
            "sunlight_exposure": round(sunlight_exposure, 2),
            "medications": medications,
            "chronic_illness": chronic_illness,
            "allergies": allergies,
            "lactose_intolerance": lactose_intolerance,
        }

        vector = [
            float(values["fatigue"]),
            float(values["diet_type"]),
            float(values["vegetarian"]),
            float(values["pregnancy"]),
            float(values["sunlight_exposure"]),
            float(values["medications"]),
            float(values["chronic_illness"]),
            float(values["allergies"]),
            float(values["lactose_intolerance"]),
        ]

        return QuestionnaireEncoding(values=values, vector=vector, synthetic=True)


def encode_questionnaire_payload(payload: Dict[str, Any], cfg: Dict[str, Any]) -> List[float]:
    diet_map = cfg["questionnaire"]["diet_type_map"]
    diet_value = payload.get("diet_type", "omnivore")
    if isinstance(diet_value, str):
        diet_encoded = diet_map.get(diet_value.lower().strip(), 0)
    else:
        diet_encoded = int(diet_value)

    return [
        float(int(bool(payload.get("fatigue", 0)))),
        float(diet_encoded),
        float(int(bool(payload.get("vegetarian", 0)))),
        float(int(bool(payload.get("pregnancy", 0)))),
        float(payload.get("sunlight_exposure", 2.0)),
        float(payload.get("medications", 0)),
        float(int(bool(payload.get("chronic_illness", 0)))),
        float(int(bool(payload.get("allergies", 0)))),
        float(int(bool(payload.get("lactose_intolerance", 0)))),
    ]
