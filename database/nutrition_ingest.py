from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd


NUTRIENT_SYNONYMS = {
    "iron_mg": ["iron", "fe"],
    "vitamin_a_ug": ["vitamin a", "retinol", "beta carotene", "carotene"],
    "vitamin_b12_ug": ["vitamin b12", "b12", "cobalamin"],
    "vitamin_b6_mg": ["vitamin b6", "b6", "pyridoxine"],
    "folate_ug": ["folate", "folic"],
    "vitamin_c_mg": ["vitamin c", "ascorbic"],
    "vitamin_d_iu": ["vitamin d", "cholecalciferol", "ergocalciferol"],
    "protein_g": ["protein"],
    "calcium_mg": ["calcium", "ca"],
    "magnesium_mg": ["magnesium", "mg"],
    "zinc_mg": ["zinc", "zn"],
    "fiber_g": ["fiber", "fibre"],
    "fat_g": ["fat", "lipid"],
}


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", str(text).lower().replace("_", " ").replace("-", " ")).strip()


def _to_number(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().lower()
    if not s:
        return default

    m = re.search(r"[-+]?\d*\.?\d+", s)
    if not m:
        return default
    return float(m.group(0))


def _find_best_column(columns: List[str], candidates: List[str]) -> Optional[str]:
    norm_cols = {_norm(c): c for c in columns}

    for cand in candidates:
        cand_norm = _norm(cand)
        for c_norm, original in norm_cols.items():
            if cand_norm == c_norm or cand_norm in c_norm:
                return original

    for cand in candidates:
        cand_norm = _norm(cand)
        for c_norm, original in norm_cols.items():
            if c_norm.startswith(cand_norm):
                return original

    return None


def _extract_food_name(row: pd.Series, columns: List[str]) -> Optional[str]:
    candidates = [
        "food",
        "food name",
        "name",
        "item",
        "dish",
        "product",
    ]
    col = _find_best_column(columns, candidates)
    if col is None:
        return None
    val = str(row.get(col, "")).strip()
    return val if val else None


def _extract_boolean_from_row(row: pd.Series, columns: List[str], tokens: List[str]) -> Optional[bool]:
    col = _find_best_column(columns, tokens)
    if col is None:
        return None

    val = str(row.get(col, "")).strip().lower()
    if val in {"1", "true", "yes", "y", "veg", "vegetarian", "vegan"}:
        return True
    if val in {"0", "false", "no", "n", "non-veg", "non vegetarian"}:
        return False
    return None


class NutritionIngestor:
    def __init__(self, cfg: Dict[str, Any], logger, mongo_gateway):
        self.cfg = cfg
        self.logger = logger
        self.mongo = mongo_gateway

    def _iter_csv_files(self, extracted_nutrition_dirs: Dict[str, Path]) -> Iterable[Tuple[str, Path]]:
        for dataset_name, root in extracted_nutrition_dirs.items():
            for fp in root.rglob("*.csv"):
                yield dataset_name, fp

    def _map_nutrients(self, row: pd.Series, columns: List[str]) -> Dict[str, float]:
        nutrients: Dict[str, float] = {}
        for target_key, candidates in NUTRIENT_SYNONYMS.items():
            col = _find_best_column(columns, candidates)
            nutrients[target_key] = _to_number(row.get(col), default=0.0) if col else 0.0
        return nutrients

    def ingest(self, extracted_nutrition_dirs: Dict[str, Path]) -> Dict[str, Any]:
        inserted = 0
        scanned_files = 0

        for dataset_name, csv_path in self._iter_csv_files(extracted_nutrition_dirs):
            scanned_files += 1
            self.logger.info("Ingesting nutrition CSV: %s", csv_path)
            try:
                df = pd.read_csv(csv_path)
            except Exception as ex:
                self.logger.warning("Failed reading %s: %s", csv_path, ex)
                continue

            if df.empty:
                continue

            columns = list(df.columns)

            for _, row in df.iterrows():
                food_name = _extract_food_name(row, columns)
                if not food_name:
                    continue

                nutrients = self._map_nutrients(row, columns)

                if sum(float(v) for v in nutrients.values()) <= 0:
                    continue

                absorption_col = _find_best_column(columns, ["absorption", "absorption rate"])
                bio_col = _find_best_column(columns, ["bioavailability", "bio available", "availability"])
                portion_col = _find_best_column(columns, ["portion", "serving", "serving size", "portion size"])

                vegetarian = _extract_boolean_from_row(row, columns, ["vegetarian", "veg", "is veg"])
                vegan = _extract_boolean_from_row(row, columns, ["vegan", "is vegan"])

                category_col = _find_best_column(columns, ["category", "group", "meal", "meal type"])
                allergen_col = _find_best_column(columns, ["allergen", "allergy", "contains"])

                allergens_val = str(row.get(allergen_col, "")).strip() if allergen_col else ""
                allergens = [a.strip().lower() for a in re.split(r"[,;/|]", allergens_val) if a.strip()]

                payload = {
                    "nutrients": nutrients,
                    "absorption_rate": max(0.05, min(1.0, _to_number(row.get(absorption_col), default=0.65)))
                    if absorption_col
                    else 0.65,
                    "bioavailability": max(0.05, min(1.0, _to_number(row.get(bio_col), default=0.60))) if bio_col else 0.60,
                    "portion_size_g": max(5.0, _to_number(row.get(portion_col), default=100.0)) if portion_col else 100.0,
                    "tags": {
                        "vegetarian": bool(vegetarian) if vegetarian is not None else None,
                        "vegan": bool(vegan) if vegan is not None else None,
                        "category": str(row.get(category_col)).strip().lower() if category_col else "",
                        "allergens": allergens,
                    },
                    "source_file": str(csv_path.as_posix()),
                }

                self.mongo.upsert_nutrition_doc(
                    food_name=food_name.strip().lower(),
                    source_dataset=dataset_name,
                    payload=payload,
                )
                inserted += 1

        summary = {
            "csv_files_scanned": scanned_files,
            "nutrition_records_upserted": inserted,
            "nutrition_collection_count": self.mongo.nutrition_count(),
        }
        self.logger.info("Nutrition ingestion summary: %s", summary)
        return summary
