from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

# Task schema for creating a new task
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    completed: bool = False

# Task schema for updating an existing task
class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None
    order_position: Optional[int] = None

# Task schema for response
class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    completed: bool
    order_position: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Allows the model to read data from ORM objects
