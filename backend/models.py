from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Status = Literal["Applied", "Interviewing", "Offer", "Rejected"]

# Statuses that still await a final answer
WAITING_STATUSES = ("Applied", "Interviewing")


class ApplicationCreate(BaseModel):
    # Trim spaces before validating, so "   " counts as empty
    model_config = ConfigDict(str_strip_whitespace=True)

    company: str = Field(min_length=1, max_length=200)
    role: str = Field(min_length=1, max_length=200)
    status: Status = "Applied"
    date_applied: date


class Application(ApplicationCreate):
    id: int


class StatusUpdate(BaseModel):
    status: Status


class Stats(BaseModel):
    total: int
    rejected: int
    waiting: int
