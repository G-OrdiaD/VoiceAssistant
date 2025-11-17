from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Task:
    id: int
    title: str
    due_time: str  # Store as string for simplicity
    created_at: str
    is_completed: bool = False