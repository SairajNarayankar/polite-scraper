"""Pydantic schema for a finished, storeable book record."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class BookRecord(BaseModel):
    title: str = Field(min_length=1)
    product_url: str
    price_text: str = Field(min_length=1)
    price_gbp: float = Field(gt=0)
    availability_text: str = Field(min_length=1)
    rating_text: str = Field(min_length=1)
    description: Optional[str] = None
    source_page: str
    fetched_at: str

    @field_validator("product_url", "source_page")
    @classmethod
    def must_be_https(cls, value: str) -> str:
        if not value.startswith("https://"):
            raise ValueError("URL must start with https://")
        return value

    @field_validator("fetched_at")
    @classmethod
    def must_be_iso_utc(cls, value: str) -> str:
        try:
            datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError as exc:
            raise ValueError("fetched_at must be ISO-8601 UTC (YYYY-MM-DDTHH:MM:SSZ)") from exc
        return value


def validate_record(raw: dict) -> tuple[BookRecord | None, str | None]:
    try:
        return BookRecord.model_validate(raw), None
    except Exception as exc:
        return None, str(exc)
