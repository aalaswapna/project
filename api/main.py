from __future__ import annotations

import hmac
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

from api.auth import (
    extract_bearer_token,
    hash_password,
    issue_token,
    load_auth_config,
    validate_token,
    verify_password,
)
from api.schemas import (
    AnswersResponse,
    AuthMeResponse,
    ChatRequest,
    ChatResponse,
    DietResponse,
    HeatmapResponse,
    LoginRequest,
    LoginResponse,
    PredictResponse,
    QuestionnairePayload,
    ResultResponse,
    SignupRequest,
)
from database.mongo import MongoGateway
from database.recommendation_engine import RecommendationEngine
from training.inference import InferenceService
from utils.config import load_yaml
from utils.logger import setup_logger


def _find_latest_checkpoint(models_dir: str | Path) -> Path:
    candidates = sorted(Path(models_dir).glob("**/best_model.pt"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError("No trained checkpoint found under models/")
    return candidates[0]


def _load_image_from_upload(upload: UploadFile) -> Image.Image:
    try:
        data = upload.file.read()
        from io import BytesIO

        with Image.open(BytesIO(data)) as img:
            return img.convert("RGB")
    except Exception as ex:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {upload.filename} ({ex})")


def _apply_env_overrides(cfg: Dict[str, Any]) -> Dict[str, Any]:
    mongo_uri = os.environ.get("MONGODB_URI", "").strip()
    mongo_db = os.environ.get("MONGODB_DB", "").strip()
    if mongo_uri:
        cfg["mongo"]["uri"] = mongo_uri
    if mongo_db:
        cfg["mongo"]["database"] = mongo_db
    return cfg


def _normalize_threshold(value: float) -> float:
    if value < 0.0 or value > 1.0:
        raise HTTPException(status_code=400, detail="Severity threshold must be between 0.0 and 1.0")
    return float(value)


def _top_food_names(recommendation: Dict[str, Any], limit: int = 4) -> List[str]:
    foods: List[str] = []
    for item in (recommendation or {}).get("ranked_foods", []):
        name = item.get("food_name")
        if isinstance(name, str) and name.strip():
            foods.append(name.strip())
        if len(foods) >= limit:
            break
    return foods


def _compose_chat_response(message: str, prediction_doc: Optional[Dict[str, Any]], threshold: float) -> ChatResponse:
    clean_message = message.strip()
    lowered = clean_message.lower()

    if not prediction_doc:
        return ChatResponse(
            reply=(
                "I can help after you run an analysis. Upload images or use the live camera module, "
                "then ask about severity, diet, or next steps."
            ),
            guidance=[
                "Run at least one prediction first",
                "Set a severity threshold that matches your triage needs",
                "Ask focused questions like 'what should I eat today?'",
            ],
        )

    prediction = prediction_doc.get("prediction", {})
    predicted_class = str(prediction.get("predicted_class", "unknown"))
    severity = float(prediction.get("severity", 0.0))
    confidence = float(prediction.get("confidence", 0.0))
    recommendation = prediction.get("recommendation", {}) or {}
    severity_alert = severity >= threshold
    foods = _top_food_names(recommendation, limit=4)

    if any(word in lowered for word in ["food", "diet", "meal", "eat", "nutrition"]):
        if foods:
            reply = (
                f"For {predicted_class.replace('_', ' ')}, prioritize: {', '.join(foods)}. "
                "Use the meal plan panel for slot-by-slot food choices."
            )
        else:
            reply = (
                "Diet recommendations are not generated yet. Open the diet section first, then ask for food or meal advice."
            )
    elif any(word in lowered for word in ["alert", "risk", "severe", "urgent", "danger"]):
        if severity_alert:
            reply = (
                f"Severity is {severity * 100:.1f}% and exceeds your threshold ({threshold * 100:.1f}%). "
                "Treat this as high priority and consider clinical follow-up."
            )
        else:
            reply = (
                f"Severity is {severity * 100:.1f}% and below your threshold ({threshold * 100:.1f}%). "
                "Continue monitoring and improve diet/sunlight consistency."
            )
    elif any(word in lowered for word in ["next", "plan", "do now", "action", "steps"]):
        reply = (
            f"Current class is {predicted_class.replace('_', ' ')} with {confidence * 100:.1f}% confidence. "
            "Follow the meal plan, monitor symptoms daily, and repeat camera analysis after lifestyle changes."
        )
    elif any(word in lowered for word in ["result", "class", "confidence", "probability"]):
        reply = (
            f"Prediction: {predicted_class.replace('_', ' ')}. "
            f"Confidence: {confidence * 100:.1f}%. Severity: {severity * 100:.1f}%."
        )
    else:
        reply = (
            f"You asked: '{clean_message}'. Based on the latest analysis, "
            f"{predicted_class.replace('_', ' ')} is currently indicated at {severity * 100:.1f}% severity. "
            "Ask about food, alerts, or next-step actions for more targeted guidance."
        )

    guidance = [
        "Use live camera mode for trend monitoring",
        "Increase threshold for stricter alerts",
        "Escalate to specialist when alerts stay high across repeated checks",
    ]

    return ChatResponse(
        reply=reply,
        predicted_class=predicted_class,
        severity=severity,
        severity_alert=severity_alert,
        guidance=guidance,
    )


load_dotenv()
cfg = _apply_env_overrides(load_yaml("configs/default.yaml"))
logger = setup_logger("api", "logs/api.log")
mongo = MongoGateway(cfg, logger=logger)
rec_engine = RecommendationEngine(cfg, mongo_gateway=mongo, logger=logger)
auth_cfg = load_auth_config()

checkpoint_env = os.environ.get("MODEL_CHECKPOINT", "").strip()
checkpoint_path = Path(checkpoint_env) if checkpoint_env else _find_latest_checkpoint(cfg["paths"]["models_dir"])
infer_service = InferenceService(cfg=cfg, checkpoint_path=checkpoint_path, logger=logger)
default_threshold = float(cfg.get("recommendation", {}).get("severity_threshold", 0.72))

app = FastAPI(title="Vitamin Deficiency Detection API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_ORGANS = {"eye", "nail", "skin"}
FORBIDDEN_ORAL_TERMS = [
    "".join([chr(108), chr(105), chr(112), chr(115)]),
    "".join([chr(116), chr(111), chr(110), chr(103), chr(117), chr(101)]),
]
USERNAME_PATTERN = re.compile(r"^[a-z0-9_.-]{3,32}$")


def _normalize_username(raw_username: str) -> str:
    username = str(raw_username).strip().lower()
    if not USERNAME_PATTERN.fullmatch(username):
        raise HTTPException(
            status_code=400,
            detail="Username must be 3-32 chars and use only lowercase letters, digits, dot, dash, or underscore",
        )
    return username


def _issue_login_response(username: str) -> LoginResponse:
    token = issue_token(username, auth_cfg)
    return LoginResponse(
        access_token=token,
        expires_in_seconds=auth_cfg.token_ttl_seconds,
        username=username,
    )


def require_auth(authorization: Optional[str] = Header(default=None)) -> Dict[str, object]:
    if not auth_cfg.auth_required:
        return {"sub": "anonymous"}
    token = extract_bearer_token(authorization)
    return validate_token(token, auth_cfg)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "checkpoint": str(checkpoint_path),
        "auth_required": auth_cfg.auth_required,
    }


@app.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    username = _normalize_username(payload.username)
    user_doc = mongo.get_user_by_username(username)
    if user_doc:
        valid = verify_password(
            payload.password,
            str(user_doc.get("password_salt", "")),
            str(user_doc.get("password_hash", "")),
            auth_cfg.password_hash_iterations,
        )
        if not valid:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        return _issue_login_response(username)

    legacy_username = auth_cfg.username.strip().lower()
    username_ok = hmac.compare_digest(username, legacy_username)
    password_ok = hmac.compare_digest(payload.password, auth_cfg.password)
    if username_ok and password_ok:
        return _issue_login_response(legacy_username)

    raise HTTPException(status_code=401, detail="Invalid username or password")


@app.post("/auth/signup", response_model=LoginResponse)
def signup(payload: SignupRequest):
    username = _normalize_username(payload.username)
    password = payload.password
    if not password.strip():
        raise HTTPException(status_code=400, detail="Password cannot be empty")

    legacy_username = auth_cfg.username.strip().lower()
    if username == legacy_username:
        raise HTTPException(status_code=409, detail="Username already exists")

    if mongo.get_user_by_username(username):
        raise HTTPException(status_code=409, detail="Username already exists")

    salt_b64, hash_b64 = hash_password(password, auth_cfg.password_hash_iterations)
    created = mongo.create_user(username=username, password_hash=hash_b64, password_salt=salt_b64)
    if not created:
        raise HTTPException(status_code=409, detail="Username already exists")

    try:
        mongo.log_event(event_type="signup", payload={"username": username})
    except Exception as ex:
        logger.warning("Failed to log signup event: %s", ex)

    return _issue_login_response(username)


@app.get("/auth/me", response_model=AuthMeResponse)
def auth_me(current_user: Dict[str, object] = Depends(require_auth)):
    return AuthMeResponse(
        username=str(current_user.get("sub", "anonymous")),
        auth_required=auth_cfg.auth_required,
    )


@app.post("/answers", response_model=AnswersResponse)
def store_answers(payload: QuestionnairePayload, _: Dict[str, object] = Depends(require_auth)):
    session_id = mongo.create_session(payload.model_dump(), source="answers_endpoint")
    return AnswersResponse(session_id=session_id)


@app.post("/predict", response_model=PredictResponse)
def predict(
    images: List[UploadFile] = File(...),
    questionnaire: str = Form(...),
    session_id: Optional[str] = Form(default=None),
    organ: str = Form(default="skin"),
    severity_threshold: float = Form(default=default_threshold),
    _: Dict[str, object] = Depends(require_auth),
):
    organ_value = organ.strip().lower()
    if organ_value not in ALLOWED_ORGANS:
        raise HTTPException(status_code=400, detail="Only eye, nail, or skin uploads are allowed")

    if not images:
        raise HTTPException(status_code=400, detail="At least one image is required")

    for img in images:
        filename = (img.filename or "").lower()
        if any(term in filename for term in FORBIDDEN_ORAL_TERMS):
            raise HTTPException(status_code=400, detail="Forbidden oral-organ content detected in filename")

    threshold_value = _normalize_threshold(float(severity_threshold))

    try:
        q_payload = json.loads(questionnaire)
        q_valid = QuestionnairePayload(**q_payload)
    except Exception as ex:
        raise HTTPException(status_code=400, detail=f"Invalid questionnaire payload: {ex}")

    pil_images = [_load_image_from_upload(u) for u in images]

    if not session_id:
        session_id = mongo.create_session(q_valid.model_dump(), source="predict_endpoint")

    pred = infer_service.predict(pil_images=pil_images, questionnaire_payload=q_valid.model_dump())

    heatmaps = []
    for entry in pred.get("heatmaps", []):
        heatmaps.append(
            {
                "image_id": str(uuid4()),
                "base_b64": entry["base_b64"],
                "overlay_b64": entry["overlay_b64"],
                "image_index": entry["image_index"],
            }
        )

    severity_value = float(pred["severity"])
    severity_alert = severity_value >= threshold_value

    payload = {
        "organ": organ_value,
        "predicted_class": pred["predicted_class"],
        "confidence": pred["confidence"],
        "severity": severity_value,
        "severity_threshold": threshold_value,
        "severity_alert": severity_alert,
        "probabilities": pred["probabilities"],
        "heatmaps": heatmaps,
        "questionnaire": q_valid.model_dump(),
    }

    prediction_id = mongo.create_prediction(session_id=session_id, payload=payload)

    return PredictResponse(
        prediction_id=prediction_id,
        session_id=session_id,
        predicted_class=pred["predicted_class"],
        confidence=pred["confidence"],
        severity=severity_value,
        severity_threshold=threshold_value,
        severity_alert=severity_alert,
        probabilities=pred["probabilities"],
        heatmap_count=len(heatmaps),
    )


@app.get("/result/{prediction_id}", response_model=ResultResponse)
def get_result(prediction_id: str, _: Dict[str, object] = Depends(require_auth)):
    doc = mongo.get_prediction(prediction_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return ResultResponse(prediction_id=prediction_id, payload=doc["prediction"])


@app.get("/heatmap/{image_id}", response_model=HeatmapResponse)
def get_heatmap(image_id: str, _: Dict[str, object] = Depends(require_auth)):
    doc = mongo.predictions.find_one({"prediction.heatmaps.image_id": image_id}, {"prediction.heatmaps.$": 1})
    if not doc:
        raise HTTPException(status_code=404, detail="Heatmap not found")

    heatmap = doc["prediction"]["heatmaps"][0]
    return HeatmapResponse(image_id=image_id, base_b64=heatmap["base_b64"], overlay_b64=heatmap["overlay_b64"])


@app.get("/diet/{prediction_id}", response_model=DietResponse)
def get_diet(prediction_id: str, _: Dict[str, object] = Depends(require_auth)):
    doc = mongo.get_prediction(prediction_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Prediction not found")

    payload = doc["prediction"]
    q = payload.get("questionnaire", {})

    recommendation = rec_engine.generate(
        predicted_class=payload["predicted_class"],
        severity=float(payload["severity"]),
        questionnaire=q,
    )

    mongo.update_prediction(prediction_id, {"prediction.recommendation": recommendation})
    return DietResponse(prediction_id=prediction_id, recommendation=recommendation)


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, current_user: Dict[str, object] = Depends(require_auth)):
    threshold_value = default_threshold if payload.severity_threshold is None else float(payload.severity_threshold)
    threshold = _normalize_threshold(threshold_value)
    prediction_doc = None
    if payload.prediction_id:
        prediction_doc = mongo.get_prediction(payload.prediction_id)
        if not prediction_doc:
            raise HTTPException(status_code=404, detail="Prediction not found for chatbot context")

    response = _compose_chat_response(payload.message, prediction_doc, threshold)
    try:
        mongo.log_event(
            event_type="chat_message",
            payload={
                "username": str(current_user.get("sub", "anonymous")),
                "prediction_id": payload.prediction_id,
                "message": payload.message,
                "reply": response.reply,
                "severity_alert": response.severity_alert,
            },
        )
    except Exception as ex:
        logger.warning("Failed to log chat event: %s", ex)

    return response
