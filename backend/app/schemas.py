from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    name: str = Field(default="", max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    name: str

    model_config = {"from_attributes": True}


class StoryPage(BaseModel):
    page: int
    text: str
    illustration_note: str


AgeBand = Literal["2-5", "5-9", "6-9", "9-12"]


class StorySummary(BaseModel):
    id: str
    title: str
    gender: Literal["boy", "girl", "unisex"]
    age_range: str
    age_bands: list[AgeBand]
    theme: str
    page_count: int


class StoryDetail(StorySummary):
    age_band: AgeBand
    pages: list[StoryPage]


class BookCreate(BaseModel):
    child_name: str = Field(min_length=1, max_length=80)
    child_age: int = Field(ge=1, le=12)
    child_gender: Literal["boy", "girl", "unisex"]


class BookOut(BaseModel):
    id: uuid.UUID
    child_name: str
    child_age: int
    child_gender: str
    story_id: str | None
    age_band: str | None = None
    suggested_age_band: AgeBand | None = None
    status: str
    progress: int
    progress_message: str
    error_message: str | None
    created_at: datetime
    has_photo: bool = False
    pdf_url: str | None = None
    page_urls: list[str] = []

    model_config = {"from_attributes": True}


class JobOut(BaseModel):
    id: uuid.UUID
    book_id: uuid.UUID
    status: str
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None

    model_config = {"from_attributes": True}


class GenerateRequest(BaseModel):
    story_id: str
    age_band: AgeBand | None = None
    age_band_mode: Literal["auto", "manual"] = "auto"
