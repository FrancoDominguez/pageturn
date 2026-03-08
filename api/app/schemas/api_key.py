from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class ApiKeyCreate(BaseModel):
    name: str


class ApiKeyResponse(BaseModel):
    id: UUID
    name: str
    key_prefix: str
    scope: str
    last_used_at: str | None = None
    created_at: str
    is_active: bool


class ApiKeyCreatedResponse(BaseModel):
    api_key: dict
    warning: str = "Save this key — you won't be able to see it again."


class ApiKeysListResponse(BaseModel):
    api_keys: list[ApiKeyResponse]
