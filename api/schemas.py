from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class QuestionnairePayload(BaseModel):
    fatigue: int = Field(0, ge=0, le=1)
    diet_type: str = "omnivore"
    vegetarian: int = Field(0, ge=0, le=1)
    pregnancy: int = Field(0, ge=0, le=1)
    sunlight_exposure: float = Field(2.0, ge=0.0, le=16.0)
    medications: int = Field(0, ge=0, le=10)
    chronic_illness: int = Field(0, ge=0, le=1)
    allergies: int = Field(0, ge=0, le=1)
    lactose_intolerance: int = Field(0, ge=0, le=1)


class AnswersResponse(BaseModel):
    session_id: str


class PredictResponse(BaseModel):
    prediction_id: str
    session_id: str
    predicted_class: str
    confidence: float
    severity: float
    severity_threshold: float
    severity_alert: bool
    probabilities: Dict[str, float]
    heatmap_count: int


class DietResponse(BaseModel):
    prediction_id: str
    recommendation: Dict[str, object]


class ResultResponse(BaseModel):
    prediction_id: str
    payload: Dict[str, object]


class HeatmapResponse(BaseModel):
    image_id: str
    base_b64: str
    overlay_b64: str


class LoginRequest(BaseModel):
    username: str
    password: str


class SignupRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)
    password: str = Field(..., min_length=8, max_length=128)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    username: str


class AuthMeResponse(BaseModel):
    username: str
    auth_required: bool


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=400)
    prediction_id: Optional[str] = None
    severity_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class ChatResponse(BaseModel):
    reply: str
    predicted_class: Optional[str] = None
    severity: Optional[float] = None
    severity_alert: bool = False
    guidance: List[str] = Field(default_factory=list)
