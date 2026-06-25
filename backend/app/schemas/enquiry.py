from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class EnquiryCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    phone_number: str = Field(min_length=4, max_length=32)
    requirement: str = Field(min_length=1, max_length=2000)
    email: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=120)
    source: Literal["linkedin", "instagram", "other"] = "other"
    language: str = Field(default="te-IN", max_length=20)


class EnquiryStartResponse(BaseModel):
    lead_id: int
    session_id: int
    token: str
    language: str
    opening_line: str
