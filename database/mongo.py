from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from bson import ObjectId
from pymongo import MongoClient


class MongoGateway:
    def __init__(self, cfg: Dict[str, Any], logger=None):
        self.logger = logger
        mongo_cfg = cfg["mongo"]
        self.backend = "mongodb"
        self.client = None
        self.db = None

        try:
            self.client = MongoClient(mongo_cfg["uri"], serverSelectionTimeoutMS=5000)
            self.client.admin.command("ping")
            self.db = self.client[mongo_cfg["database"]]
        except Exception as ex:
            try:
                from mongita import MongitaClientDisk
            except Exception as fallback_ex:
                raise RuntimeError(
                    "MongoDB unavailable and Mongita fallback not installed. "
                    "Install mongita or start MongoDB on localhost:27017."
                ) from fallback_ex

            Path("data/local_mongo").mkdir(parents=True, exist_ok=True)
            self.client = MongitaClientDisk()
            self.db = self.client[mongo_cfg["database"]]
            self.backend = "mongita"
            if self.logger:
                self.logger.warning(
                    "MongoDB is unreachable; using Mongita disk fallback for local persistence: %s",
                    ex,
                )

        cols = mongo_cfg["collections"]
        self.sessions = self.db[cols["sessions"]]
        self.predictions = self.db[cols["predictions"]]
        self.nutrition = self.db[cols["nutrition"]]
        self.logs = self.db[cols["logs"]]
        self.users = self.db[cols.get("users", "users")]

        try:
            self.sessions.create_index("created_at")
            self.predictions.create_index("created_at")
            self.nutrition.create_index("food_name")
            self.users.create_index("username", unique=True)
        except Exception:
            # Indexing support varies across local fallback engines.
            pass

    @staticmethod
    def _oid(value: str | ObjectId) -> Any:
        if isinstance(value, ObjectId):
            return value
        try:
            return ObjectId(value)
        except Exception:
            return value

    def log_event(self, event_type: str, payload: Dict[str, Any]) -> str:
        doc = {
            "event_type": event_type,
            "payload": payload,
            "created_at": datetime.now(timezone.utc),
        }
        result = self.logs.insert_one(doc)
        return str(result.inserted_id)

    def create_session(self, questionnaire: Dict[str, Any], source: str = "api") -> str:
        doc = {
            "questionnaire": questionnaire,
            "source": source,
            "created_at": datetime.now(timezone.utc),
        }
        result = self.sessions.insert_one(doc)
        return str(result.inserted_id)

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        doc = self.sessions.find_one({"_id": self._oid(session_id)})
        if not doc:
            return None
        doc["_id"] = str(doc["_id"])
        return doc

    def create_prediction(self, session_id: str, payload: Dict[str, Any]) -> str:
        doc = {
            "session_id": session_id,
            "prediction": payload,
            "created_at": datetime.now(timezone.utc),
        }
        result = self.predictions.insert_one(doc)
        return str(result.inserted_id)

    def update_prediction(self, prediction_id: str, payload: Dict[str, Any]) -> None:
        self.predictions.update_one({"_id": self._oid(prediction_id)}, {"$set": payload})

    def get_prediction(self, prediction_id: str) -> Optional[Dict[str, Any]]:
        doc = self.predictions.find_one({"_id": self._oid(prediction_id)})
        if not doc:
            return None
        doc["_id"] = str(doc["_id"])
        return doc

    def nutrition_count(self) -> int:
        return self.nutrition.count_documents({})

    def upsert_nutrition_doc(self, food_name: str, source_dataset: str, payload: Dict[str, Any]) -> None:
        key = {"food_name": food_name, "source_dataset": source_dataset}
        doc = {
            **payload,
            "food_name": food_name,
            "source_dataset": source_dataset,
            "updated_at": datetime.now(timezone.utc),
        }
        if self.backend == "mongita":
            self.nutrition.replace_one(key, doc, upsert=True)
            return
        self.nutrition.update_one(key, {"$set": doc}, upsert=True)

    def query_nutrition(self, query: Dict[str, Any], limit: int = 3000):
        return list(self.nutrition.find(query).limit(limit))

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        doc = self.users.find_one({"username": username})
        if not doc:
            return None
        doc["_id"] = str(doc["_id"])
        return doc

    def create_user(self, username: str, password_hash: str, password_salt: str) -> bool:
        if self.users.find_one({"username": username}):
            return False

        doc = {
            "username": username,
            "password_hash": password_hash,
            "password_salt": password_salt,
            "created_at": datetime.now(timezone.utc),
        }
        try:
            self.users.insert_one(doc)
            return True
        except Exception as ex:
            if "duplicate key" in str(ex).lower():
                return False
            raise
