from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

Status = Literal["Applied", "Interviewing", "Offer", "Rejected"]

# Statuses that still await a final answer
WAITING_STATUSES = ("Applied", "Interviewing")


class ApplicationCreate(BaseModel):
    company: str = Field(min_length=1, max_length=200)
    role: str = Field(min_length=1, max_length=200)
    status: Status = "Applied"
    date_applied: date


class Application(ApplicationCreate):
    id: int


class Stats(BaseModel):
    total: int
    rejected: int
    waiting: int
