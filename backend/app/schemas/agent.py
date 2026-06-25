from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AgentBase(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    script_key: str = Field(min_length=2, max_length=120)
    vertical: str | None = Field(default=None, max_length=120)
    language: str = Field(default="te-IN", min_length=2, max_length=20)
    voice_provider: str = Field(default="sarvam", min_length=2, max_length=60)
    telephony_provider: str = Field(default="mock", min_length=2, max_length=60)
    description: str | None = None
    opening_line: str | None = None
    qualification_goal: str | None = None
    is_active: bool = True


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    script_key: str | None = Field(default=None, min_length=2, max_length=120)
    vertical: str | None = Field(default=None, max_length=120)
    language: str | None = Field(default=None, min_length=2, max_length=20)
    voice_provider: str | None = Field(default=None, min_length=2, max_length=60)
    telephony_provider: str | None = Field(default=None, min_length=2, max_length=60)
    description: str | None = None
    opening_line: str | None = None
    qualification_goal: str | None = None
    is_active: bool | None = None


class AgentRead(AgentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class AgentListResponse(BaseModel):
    items: list[AgentRead]
    total: int

