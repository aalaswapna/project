from __future__ import annotations

import copy
import re
from typing import Any, Dict, List, Tuple


def _bool(value: Any) -> bool:
    return bool(int(value)) if isinstance(value, (int, float, str)) and str(value).strip() != "" else bool(value)


def _norm_name(value: str) -> str:
    return re.sub(r"\s+", " ", str(value).strip().lower())


FALLBACK_FOOD_CATALOG: List[Dict[str, Any]] = [
    {
        "food_name": "spinach",
        "tags": {"vegetarian": True, "vegan": True, "category": "leafy"},
        "nutrients": {
            "iron_mg": 2.7,
            "vitamin_a_ug": 469.0,
            "vitamin_b12_ug": 0.0,
            "vitamin_b6_mg": 0.2,
            "folate_ug": 194.0,
            "vitamin_c_mg": 28.1,
            "vitamin_d_iu": 0.0,
            "protein_g": 2.9,
            "calcium_mg": 99.0,
            "magnesium_mg": 79.0,
            "zinc_mg": 0.5,
            "fiber_g": 2.2,
            "fat_g": 0.4,
        },
    },
    {
        "food_name": "kale",
        "tags": {"vegetarian": True, "vegan": True, "category": "leafy"},
        "nutrients": {
            "iron_mg": 1.5,
            "vitamin_a_ug": 241.0,
            "vitamin_b12_ug": 0.0,
            "vitamin_b6_mg": 0.3,
            "folate_ug": 62.0,
            "vitamin_c_mg": 120.0,
            "vitamin_d_iu": 0.0,
            "protein_g": 4.3,
            "calcium_mg": 150.0,
            "magnesium_mg": 47.0,
            "zinc_mg": 0.4,
            "fiber_g": 4.1,
            "fat_g": 0.9,
        },
    },
    {
        "food_name": "broccoli",
        "tags": {"vegetarian": True, "vegan": True, "category": "vegetable"},
        "nutrients": {
            "iron_mg": 0.7,
            "vitamin_a_ug": 31.0,
            "vitamin_b12_ug": 0.0,
            "vitamin_b6_mg": 0.2,
            "folate_ug": 63.0,
            "vitamin_c_mg": 89.2,
            "vitamin_d_iu": 0.0,
            "protein_g": 2.8,
            "calcium_mg": 47.0,
            "magnesium_mg": 21.0,
            "zinc_mg": 0.4,
            "fiber_g": 2.6,
            "fat_g": 0.4,
        },
    },
    {
        "food_name": "orange",
        "tags": {"vegetarian": True, "vegan": True, "category": "fruit"},
        "nutrients": {
            "iron_mg": 0.1,
            "vitamin_a_ug": 11.0,
            "vitamin_b12_ug": 0.0,
            "vitamin_b6_mg": 0.1,
            "folate_ug": 30.0,
            "vitamin_c_mg": 53.2,
            "vitamin_d_iu": 0.0,
            "protein_g": 0.9,
            "calcium_mg": 40.0,
            "magnesium_mg": 10.0,
            "zinc_mg": 0.1,
            "fiber_g": 2.4,
            "fat_g": 0.1,
        },
    },
    {
        "food_name": "guava",
        "tags": {"vegetarian": True, "vegan": True, "category": "fruit"},
        "nutrients": {
            "iron_mg": 0.3,
            "vitamin_a_ug": 31.0,
            "vitamin_b12_ug": 0.0,
            "vitamin_b6_mg": 0.1,
            "folate_ug": 49.0,
            "vitamin_c_mg": 228.3,
            "vitamin_d_iu": 0.0,
            "protein_g": 2.6,
            "calcium_mg": 18.0,
            "magnesium_mg": 22.0,
            "zinc_mg": 0.2,
            "fiber_g": 5.4,
            "fat_g": 1.0,
        },
    },
    {
        "food_name": "lentils",
        "tags": {"vegetarian": True, "vegan": True, "category": "legume"},
        "nutrients": {
            "iron_mg": 3.3,
            "vitamin_a_ug": 8.0,
            "vitamin_b12_ug": 0.0,
            "vitamin_b6_mg": 0.2,
            "folate_ug": 181.0,
            "vitamin_c_mg": 1.5,
            "vitamin_d_iu": 0.0,
            "protein_g": 9.0,
            "calcium_mg": 19.0,
            "magnesium_mg": 36.0,
            "zinc_mg": 1.3,
            "fiber_g": 7.9,
            "fat_g": 0.4,
        },
    },
    {
        "food_name": "chickpeas",
        "tags": {"vegetarian": True, "vegan": True, "category": "legume"},
        "nutrients": {
            "iron_mg": 2.9,
            "vitamin_a_ug": 1.0,
            "vitamin_b12_ug": 0.0,
            "vitamin_b6_mg": 0.1,
            "folate_ug": 172.0,
            "vitamin_c_mg": 1.3,
            "vitamin_d_iu": 0.0,
            "protein_g": 8.9,
            "calcium_mg": 49.0,
            "magnesium_mg": 48.0,
            "zinc_mg": 1.5,
            "fiber_g": 7.6,
            "fat_g": 2.6,
        },
    },
    {
        "food_name": "tofu",
        "tags": {"vegetarian": True, "vegan": True, "category": "protein"},
        "nutrients": {
            "iron_mg": 2.7,
            "vitamin_a_ug": 0.0,
            "vitamin_b12_ug": 0.0,
            "vitamin_b6_mg": 0.1,
            "folate_ug": 27.0,
            "vitamin_c_mg": 0.1,
            "vitamin_d_iu": 0.0,
            "protein_g": 8.0,
            "calcium_mg": 350.0,
            "magnesium_mg": 30.0,
            "zinc_mg": 1.0,
            "fiber_g": 1.0,
            "fat_g": 4.8,
        },
    },
    {
        "food_name": "pumpkin seeds",
        "tags": {"vegetarian": True, "vegan": True, "category": "seed"},
        "nutrients": {
            "iron_mg": 8.8,
            "vitamin_a_ug": 16.0,
            "vitamin_b12_ug": 0.0,
            "vitamin_b6_mg": 0.1,
            "folate_ug": 58.0,
            "vitamin_c_mg": 1.9,
            "vitamin_d_iu": 0.0,
            "protein_g": 30.0,
            "calcium_mg": 46.0,
            "magnesium_mg": 592.0,
            "zinc_mg": 7.6,
            "fiber_g": 6.0,
            "fat_g": 49.0,
        },
    },
    {
        "food_name": "egg yolk",
        "tags": {"vegetarian": False, "vegan": False, "category": "protein"},
        "nutrients": {
            "iron_mg": 2.7,
            "vitamin_a_ug": 381.0,
            "vitamin_b12_ug": 1.1,
            "vitamin_b6_mg": 0.3,
            "folate_ug": 146.0,
            "vitamin_c_mg": 0.0,
            "vitamin_d_iu": 218.0,
            "protein_g": 15.9,
            "calcium_mg": 129.0,
            "magnesium_mg": 5.0,
            "zinc_mg": 2.3,
            "fiber_g": 0.0,
            "fat_g": 26.5,
        },
    },
    {
        "food_name": "salmon",
        "tags": {"vegetarian": False, "vegan": False, "category": "protein", "allergens": ["fish"]},
        "nutrients": {
            "iron_mg": 0.8,
            "vitamin_a_ug": 50.0,
            "vitamin_b12_ug": 3.2,
            "vitamin_b6_mg": 0.6,
            "folate_ug": 25.0,
            "vitamin_c_mg": 3.9,
            "vitamin_d_iu": 526.0,
            "protein_g": 20.4,
            "calcium_mg": 9.0,
            "magnesium_mg": 29.0,
            "zinc_mg": 0.6,
            "fiber_g": 0.0,
            "fat_g": 13.4,
        },
    },
    {
        "food_name": "sardines",
        "tags": {"vegetarian": False, "vegan": False, "category": "protein", "allergens": ["fish"]},
        "nutrients": {
            "iron_mg": 2.9,
            "vitamin_a_ug": 32.0,
            "vitamin_b12_ug": 8.9,
            "vitamin_b6_mg": 0.2,
            "folate_ug": 10.0,
            "vitamin_c_mg": 0.0,
            "vitamin_d_iu": 272.0,
            "protein_g": 24.6,
            "calcium_mg": 382.0,
            "magnesium_mg": 39.0,
            "zinc_mg": 1.3,
            "fiber_g": 0.0,
            "fat_g": 11.5,
        },
    },
    {
        "food_name": "chicken liver",
        "tags": {"vegetarian": False, "vegan": False, "category": "organ"},
        "nutrients": {
            "iron_mg": 9.0,
            "vitamin_a_ug": 3296.0,
            "vitamin_b12_ug": 16.6,
            "vitamin_b6_mg": 0.9,
            "folate_ug": 588.0,
            "vitamin_c_mg": 17.9,
            "vitamin_d_iu": 49.0,
            "protein_g": 16.9,
            "calcium_mg": 11.0,
            "magnesium_mg": 18.0,
            "zinc_mg": 2.7,
            "fiber_g": 0.0,
            "fat_g": 4.8,
        },
    },
    {
        "food_name": "fortified milk",
        "tags": {"vegetarian": True, "vegan": False, "category": "dairy", "allergens": ["dairy", "lactose"]},
        "nutrients": {
            "iron_mg": 0.0,
            "vitamin_a_ug": 46.0,
            "vitamin_b12_ug": 0.4,
            "vitamin_b6_mg": 0.0,
            "folate_ug": 5.0,
            "vitamin_c_mg": 0.0,
            "vitamin_d_iu": 120.0,
            "protein_g": 3.4,
            "calcium_mg": 120.0,
            "magnesium_mg": 11.0,
            "zinc_mg": 0.4,
            "fiber_g": 0.0,
            "fat_g": 3.2,
        },
    },
    {
        "food_name": "greek yogurt",
        "tags": {"vegetarian": True, "vegan": False, "category": "dairy", "allergens": ["dairy", "lactose"]},
        "nutrients": {
            "iron_mg": 0.1,
            "vitamin_a_ug": 27.0,
            "vitamin_b12_ug": 0.5,
            "vitamin_b6_mg": 0.1,
            "folate_ug": 7.0,
            "vitamin_c_mg": 0.9,
            "vitamin_d_iu": 44.0,
            "protein_g": 10.0,
            "calcium_mg": 110.0,
            "magnesium_mg": 11.0,
            "zinc_mg": 0.5,
            "fiber_g": 0.0,
            "fat_g": 3.8,
        },
    },
    {
        "food_name": "mushrooms",
        "tags": {"vegetarian": True, "vegan": True, "category": "vegetable"},
        "nutrients": {
            "iron_mg": 0.5,
            "vitamin_a_ug": 0.0,
            "vitamin_b12_ug": 0.0,
            "vitamin_b6_mg": 0.1,
            "folate_ug": 17.0,
            "vitamin_c_mg": 2.1,
            "vitamin_d_iu": 28.0,
            "protein_g": 3.1,
            "calcium_mg": 3.0,
            "magnesium_mg": 9.0,
            "zinc_mg": 0.5,
            "fiber_g": 1.0,
            "fat_g": 0.3,
        },
    },
    {
        "food_name": "oats",
        "tags": {"vegetarian": True, "vegan": True, "category": "whole_grain"},
        "nutrients": {
            "iron_mg": 4.3,
            "vitamin_a_ug": 0.0,
            "vitamin_b12_ug": 0.0,
            "vitamin_b6_mg": 0.1,
            "folate_ug": 32.0,
            "vitamin_c_mg": 0.0,
            "vitamin_d_iu": 0.0,
            "protein_g": 16.9,
            "calcium_mg": 54.0,
            "magnesium_mg": 177.0,
            "zinc_mg": 4.0,
            "fiber_g": 10.6,
            "fat_g": 6.9,
        },
    },
    {
        "food_name": "almonds",
        "tags": {"vegetarian": True, "vegan": True, "category": "nut", "allergens": ["nuts"]},
        "nutrients": {
            "iron_mg": 3.7,
            "vitamin_a_ug": 1.0,
            "vitamin_b12_ug": 0.0,
            "vitamin_b6_mg": 0.1,
            "folate_ug": 44.0,
            "vitamin_c_mg": 0.0,
            "vitamin_d_iu": 0.0,
            "protein_g": 21.2,
            "calcium_mg": 269.0,
            "magnesium_mg": 270.0,
            "zinc_mg": 3.1,
            "fiber_g": 12.5,
            "fat_g": 49.9,
        },
    },
    {
        "food_name": "banana",
        "tags": {"vegetarian": True, "vegan": True, "category": "fruit"},
        "nutrients": {
            "iron_mg": 0.3,
            "vitamin_a_ug": 3.0,
            "vitamin_b12_ug": 0.0,
            "vitamin_b6_mg": 0.4,
            "folate_ug": 20.0,
            "vitamin_c_mg": 8.7,
            "vitamin_d_iu": 0.0,
            "protein_g": 1.1,
            "calcium_mg": 5.0,
            "magnesium_mg": 27.0,
            "zinc_mg": 0.2,
            "fiber_g": 2.6,
            "fat_g": 0.3,
        },
    },
    {
        "food_name": "sweet potato",
        "tags": {"vegetarian": True, "vegan": True, "category": "vegetable"},
        "nutrients": {
            "iron_mg": 0.6,
            "vitamin_a_ug": 709.0,
            "vitamin_b12_ug": 0.0,
            "vitamin_b6_mg": 0.2,
            "folate_ug": 11.0,
            "vitamin_c_mg": 2.4,
            "vitamin_d_iu": 0.0,
            "protein_g": 1.6,
            "calcium_mg": 30.0,
            "magnesium_mg": 25.0,
            "zinc_mg": 0.3,
            "fiber_g": 3.0,
            "fat_g": 0.1,
        },
    },
]

POSITIVE_FOOD_TOKENS = {
    "spinach",
    "kale",
    "broccoli",
    "lentil",
    "chickpea",
    "salmon",
    "sardine",
    "tofu",
    "oat",
    "sweet potato",
    "orange",
    "guava",
    "banana",
    "yogurt",
    "milk",
    "seed",
    "almond",
}

NEGATIVE_FOOD_TOKENS = {
    "cake",
    "cookie",
    "cand",
    "chocolate",
    "syrup",
    "soda",
    "cola",
    "fries",
    "roll",
    "pastry",
    "ice cream",
    "doughnut",
    "burger",
    "cinnamon roll",
    "muffin",
    "brownie",
    "frost",
    "banana bread",
    "relish",
    "sauce",
}

DAIRY_TOKENS = {"milk", "cheese", "paneer", "yogurt", "curd", "cream", "butter"}
ANIMAL_TOKENS = {
    "beef",
    "pork",
    "chicken",
    "fish",
    "lamb",
    "mutton",
    "turkey",
    "bacon",
    "shrimp",
    "egg",
    "liver",
    "salmon",
    "sardine",
}


class RecommendationEngine:
    def __init__(self, cfg: Dict[str, Any], mongo_gateway, logger):
        self.cfg = cfg
        self.mongo = mongo_gateway
        self.logger = logger

        rec_cfg = cfg["recommendation"]
        self.deficiency_map = rec_cfg["deficiency_to_nutrients"]
        self.weights = rec_cfg["scoring_weights"]
        self.upper_limits = rec_cfg["upper_limits"]
        self.severity_threshold = float(rec_cfg["severity_threshold"])
        self._fallback_docs = self._build_fallback_docs()

    def _build_fallback_docs(self) -> List[Dict[str, Any]]:
        docs: List[Dict[str, Any]] = []
        for row in FALLBACK_FOOD_CATALOG:
            tags = row.get("tags", {}) or {}
            tags = {
                "vegetarian": tags.get("vegetarian"),
                "vegan": tags.get("vegan"),
                "category": str(tags.get("category", "")).strip().lower(),
                "allergens": [str(x).strip().lower() for x in tags.get("allergens", []) if str(x).strip()],
            }
            docs.append(
                {
                    "food_name": _norm_name(row.get("food_name", "unknown")),
                    "nutrients": dict(row.get("nutrients", {})),
                    "absorption_rate": float(row.get("absorption_rate", 0.72)),
                    "bioavailability": float(row.get("bioavailability", 0.68)),
                    "portion_size_g": float(row.get("portion_size_g", 100.0)),
                    "tags": tags,
                    "source_dataset": "fallback_catalog",
                }
            )
        return docs

    def _filter_by_diet(self, docs: List[Dict[str, Any]], questionnaire: Dict[str, Any], strict_allergy: bool) -> List[Dict[str, Any]]:
        diet_type = str(questionnaire.get("diet_type", "omnivore")).strip().lower()
        vegetarian_required = _bool(questionnaire.get("vegetarian", 0)) or diet_type in {"vegetarian", "vegan"}
        vegan_required = diet_type == "vegan"
        lactose = _bool(questionnaire.get("lactose_intolerance", 0))
        allergies = _bool(questionnaire.get("allergies", 0))

        filtered: List[Dict[str, Any]] = []
        for doc in docs:
            tags = doc.get("tags", {}) or {}
            food_name = _norm_name(str(doc.get("food_name", "")))
            allergens = [str(x).strip().lower() for x in tags.get("allergens", []) if str(x).strip()]

            if vegan_required:
                if tags.get("vegan") is False:
                    continue
                if any(tok in food_name for tok in ANIMAL_TOKENS):
                    continue
                if any(dtok in food_name for dtok in DAIRY_TOKENS):
                    continue
            elif vegetarian_required:
                if tags.get("vegetarian") is False:
                    continue
                if any(tok in food_name for tok in ANIMAL_TOKENS):
                    continue

            if lactose:
                if "dairy" in allergens or "lactose" in allergens:
                    continue
                if any(dtok in food_name for dtok in DAIRY_TOKENS):
                    continue

            if allergies and strict_allergy and allergens:
                continue

            filtered.append(doc)

        return filtered

    @staticmethod
    def _quality_adjustment(food_name: str) -> float:
        lower = _norm_name(food_name)
        bonus = 0.0
        if any(tok in lower for tok in POSITIVE_FOOD_TOKENS):
            bonus += 0.14
        if any(tok in lower for tok in NEGATIVE_FOOD_TOKENS):
            bonus -= 0.28
        return bonus

    def _food_score(
        self,
        food_doc: Dict[str, Any],
        nutrient_weights: Dict[str, float],
        questionnaire: Dict[str, Any],
    ) -> Tuple[float, Dict[str, float], Dict[str, float]]:
        nutrients = food_doc.get("nutrients", {}) or {}

        nutrient_density = 0.0
        nutrient_contrib: Dict[str, float] = {}
        normalized_contrib: Dict[str, float] = {}
        covered = 0

        for nutrient, weight in nutrient_weights.items():
            value = float(nutrients.get(nutrient, 0.0))
            ul = float(self.upper_limits.get(nutrient, max(1.0, value)))
            normalized = min(1.0, value / max(ul, 1e-6))
            c = float(weight) * normalized
            nutrient_density += c
            nutrient_contrib[nutrient] = round(value, 4)
            normalized_contrib[nutrient] = round(normalized, 4)
            if value > 0:
                covered += 1

        coverage_ratio = covered / max(len(nutrient_weights), 1)
        absorption_rate = float(food_doc.get("absorption_rate", 0.65))
        bioavailability = float(food_doc.get("bioavailability", 0.60))
        portion_size = float(food_doc.get("portion_size_g", 100.0))
        portion_adj = max(0.2, min(1.5, 100.0 / max(portion_size, 1.0)))

        user_constraint_component = 1.0
        sunlight = float(questionnaire.get("sunlight_exposure", 2.0))
        if sunlight < 1.0 and "vitamin_d_iu" in nutrient_weights:
            user_constraint_component += 0.15

        total_score = (
            self.weights["nutrient_density"] * nutrient_density
            + self.weights["absorption_rate"] * absorption_rate
            + self.weights["bioavailability"] * bioavailability
            + self.weights["portion_size_adjustment"] * portion_adj
            + self.weights["user_constraints"] * user_constraint_component
            + 0.10 * coverage_ratio
            + self._quality_adjustment(str(food_doc.get("food_name", "")))
        )

        return float(total_score), nutrient_contrib, normalized_contrib

    @staticmethod
    def _bucket(food: Dict[str, Any]) -> str:
        tags = food.get("tags", {}) or {}
        category = str(tags.get("category", "")).strip().lower()
        if category:
            return category
        name = _norm_name(str(food.get("food_name", "")))
        if any(tok in name for tok in ["snack", "nut", "seed", "fruit"]):
            return "snack"
        if any(tok in name for tok in ["milk", "yogurt", "cheese", "paneer"]):
            return "dairy"
        if any(tok in name for tok in ["rice", "bread", "oat", "grain"]):
            return "grain"
        if any(tok in name for tok in ["chicken", "fish", "egg", "tofu", "lentil", "chickpea", "bean", "liver"]):
            return "protein"
        return "general"

    def _build_meal_plan(self, ranked_foods: List[Dict[str, Any]], nutrient_weights: Dict[str, float]) -> Dict[str, Dict[str, Any]]:
        slots = ["breakfast", "lunch", "dinner", "snack_1", "snack_2"]
        plan: Dict[str, Dict[str, Any]] = {}
        cumulative = {k: 0.0 for k in nutrient_weights.keys()}
        used_names = set()
        used_buckets = set()

        if not ranked_foods:
            return {slot: {"food_name": "no_safe_option_found", "score": 0.0, "nutrients": {}} for slot in slots}

        for slot in slots:
            picked = None
            for candidate in ranked_foods:
                name = str(candidate.get("food_name", "unknown"))
                bucket = str(candidate.get("bucket", "general"))
                if name in used_names:
                    continue

                # Prefer meal diversity, but do not block recommendation if pool is narrow.
                if bucket in used_buckets and len(used_buckets) < 4:
                    continue

                exceeds = False
                for nutrient in nutrient_weights:
                    val = float(candidate["nutrients"].get(nutrient, 0.0))
                    ul = float(self.upper_limits.get(nutrient, 1e12))
                    if cumulative[nutrient] + val > (1.35 * ul):
                        exceeds = True
                        break
                if exceeds:
                    continue

                picked = candidate
                break

            # Relaxation path: allow duplicate category or duplicate food instead of returning no option.
            if picked is None:
                for candidate in ranked_foods:
                    name = str(candidate.get("food_name", "unknown"))
                    if name not in used_names:
                        picked = candidate
                        break

            if picked is None:
                picked = ranked_foods[len(plan) % len(ranked_foods)]

            name = str(picked.get("food_name", "unknown"))
            bucket = str(picked.get("bucket", "general"))
            used_names.add(name)
            used_buckets.add(bucket)
            for nutrient in nutrient_weights:
                cumulative[nutrient] += float(picked["nutrients"].get(nutrient, 0.0))

            plan[slot] = {
                "food_name": name,
                "score": round(float(picked.get("score", 0.0)), 6),
                "nutrients": picked.get("nutrients", {}),
                "category": bucket,
            }

        return plan

    def _safe_query_nutrition(self, limit: int) -> List[Dict[str, Any]]:
        try:
            docs = self.mongo.query_nutrition({}, limit=limit)
            if docs:
                return docs
        except Exception as ex:
            self.logger.warning("Nutrition query failed; switching to fallback catalog: %s", ex)
        return []

    def generate(self, predicted_class: str, severity: float, questionnaire: Dict[str, Any], top_k: int = 30) -> Dict[str, Any]:
        nutrient_weights = self.deficiency_map.get(predicted_class)
        if not nutrient_weights:
            nutrient_weights = self.deficiency_map.get("other_deficiency", {})

        docs = self._safe_query_nutrition(limit=7000)
        data_source = "mongo"
        if not docs:
            docs = copy.deepcopy(self._fallback_docs)
            data_source = "fallback_catalog"
        else:
            # Blend curated foods into ranking to keep recommendations clinically sensible
            # even when raw datasets contain noisy/processed items.
            docs = list(docs) + copy.deepcopy(self._fallback_docs)

        strict_docs = self._filter_by_diet(docs, questionnaire, strict_allergy=True)
        filter_mode = "strict"

        if not strict_docs:
            strict_docs = self._filter_by_diet(docs, questionnaire, strict_allergy=False)
            filter_mode = "relaxed_allergy"

        if not strict_docs:
            strict_docs = list(docs)
            filter_mode = "unfiltered_fallback"

        if not strict_docs:
            strict_docs = copy.deepcopy(self._fallback_docs)
            data_source = "fallback_catalog"
            filter_mode = "fallback_catalog"

        deduped: Dict[str, Dict[str, Any]] = {}
        for doc in strict_docs:
            name = _norm_name(str(doc.get("food_name", "")))
            if not name:
                continue
            # Prefer the first document encountered for each food name for deterministic output.
            if name not in deduped:
                d = dict(doc)
                d["food_name"] = name
                d["tags"] = d.get("tags", {}) or {}
                d["source_dataset"] = d.get("source_dataset", data_source)
                deduped[name] = d

        ranked: List[Dict[str, Any]] = []
        for doc in deduped.values():
            score, nutrients, normalized = self._food_score(doc, nutrient_weights, questionnaire)
            ranked.append(
                {
                    "food_name": doc.get("food_name", "unknown"),
                    "score": score,
                    "nutrients": nutrients,
                    "normalized_nutrients": normalized,
                    "source_dataset": doc.get("source_dataset", ""),
                    "portion_size_g": float(doc.get("portion_size_g", 100.0)),
                    "bucket": self._bucket(doc),
                    "tags": doc.get("tags", {}) or {},
                }
            )

        ranked.sort(key=lambda x: x["score"], reverse=True)
        top_k = max(15, int(top_k))
        top_ranked = ranked[:top_k]

        meal_plan = self._build_meal_plan(top_ranked, nutrient_weights)

        advice = "Maintain nutrition plan and follow-up in 4-6 weeks."
        consult_specialist = False
        if severity >= self.severity_threshold:
            advice = (
                "High-risk profile detected. Seek clinical consultation with an internal medicine or nutrition specialist "
                "for confirmatory labs and supervised treatment."
            )
            consult_specialist = True

        if filter_mode != "strict":
            advice = f"{advice} Recommendation mode used: {filter_mode.replace('_', ' ')}."

        return {
            "predicted_deficiency": predicted_class,
            "severity": round(float(severity), 4),
            "required_nutrients": nutrient_weights,
            "ranked_foods": top_ranked,
            "meal_plan": meal_plan,
            "medical_advice": advice,
            "consult_specialist": consult_specialist,
            "candidate_pool_size": len(ranked),
            "data_source": data_source,
            "filter_mode": filter_mode,
        }
