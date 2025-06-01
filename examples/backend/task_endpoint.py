"""
Task Endpoint - FastAPI Backend Example

This file demonstrates:
- Request validation with Pydantic models
- Authentication handling
- Database operations with Supabase
- Error handling and response formatting

This endpoint handles complex business logic that would be inefficient
to implement in the frontend or Next.js API routes.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
from uuid import UUID

# Import database and authentication utilities
from app.db.session import get_db
from app.core.auth import get_current_user
from app.core.security import verify_token
from app.models.user import User
from app.services import task_service
from app.core.config import settings

# Create router
router = APIRouter(prefix="/api/tasks", tags=["tasks"])

# Define Pydantic models for request/response validation

class TaskBase(BaseModel):
    """Base model with common task attributes"""
    title: str
    description: Optional[str] = None
    priority: Optional[str] = "none"
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = []
    
    @validator("priority")
    def validate_priority(cls, v):
        """Validate that priority is one of the allowed values"""
        allowed_priorities = ["none", "low", "medium", "high"]
        if v not in allowed_priorities:
            raise ValueError(f"Priority must be one of: {', '.join(allowed_priorities)}")
        return v

class TaskCreate(TaskBase):
    """Model for creating a new task"""
    pass

class TaskUpdate(BaseModel):
    """Model for updating an existing task"""
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = None
    
    @validator("priority")
    def validate_priority(cls, v):
        """Validate that priority is one of the allowed values"""
        if v is None:
            return v
        allowed_priorities = ["none", "low", "medium", "high"]
        if v not in allowed_priorities:
            raise ValueError(f"Priority must be one of: {', '.join(allowed_priorities)}")
        return v

class TaskInDB(TaskBase):
    """Model for a task as stored in the database"""
    id: UUID
    user_id: UUID
    completed: bool = False
    order_position: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

class TaskResponse(TaskInDB):
    """Model for task response"""
    class Config:
        orm_mode = True

class TaskAnalytics(BaseModel):
    """Model for task analytics response"""
    total_tasks: int
    completed_tasks: int
    completion_rate: float
    average_completion_time: Optional[float] = None
    tasks_by_priority: Dict[str, int]
    tasks_by_tag: Dict[str, int]
    overdue_tasks: int

class ErrorResponse(BaseModel):
    """Model for error responses"""
    detail: str
    code: Optional[str] = None

# Authentication dependency
async def get_user_from_header(x_user_id: str = Header(None)):
    """
    Get user from the X-User-ID header
    
    This is a simplified authentication method for the example.
    In a real application, you would use JWT tokens or another secure method.
    """
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # In a real application, you would validate the user ID
    # For this example, we'll just return it
    return x_user_id

# Database connection dependency
def get_supabase_client():
    """
    Get a Supabase client for database operations
    
    This demonstrates how to connect to Supabase from FastAPI
    """
    from supabase import create_client
    
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_SERVICE_ROLE_KEY
    
    return create_client(url, key)

# Endpoints

@router.get("/", response_model=List[TaskResponse], responses={401: {"model": ErrorResponse}})
async def get_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    user_id: str = Depends(get_user_from_header),
    supabase = Depends(get_supabase_client)
):
    """
    Get all tasks for the current user
    
    This endpoint demonstrates:
    - Pagination with skip/limit
    - Authentication with user_id header
    - Direct Supabase database access
    """
    try:
        # Query tasks from Supabase
        response = supabase.table("tasks") \
            .select("*") \
            .eq("user_id", user_id) \
            .order("order_position", {"ascending": True}) \
            .range(skip, skip + limit - 1) \
            .execute()
        
        # Return the tasks
        return response.data
    except Exception as e:
        # Log the error
        print(f"Error fetching tasks: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch tasks")

@router.get("/{task_id}", response_model=TaskResponse, responses={
    401: {"model": ErrorResponse},
    404: {"model": ErrorResponse}
})
async def get_task(
    task_id: UUID,
    user_id: str = Depends(get_user_from_header),
    supabase = Depends(get_supabase_client)
):
    """
    Get a single task by ID
    
    This endpoint demonstrates:
    - Path parameters
    - Error handling for not found resources
    - Ownership validation
    """
    try:
        # Query the task from Supabase
        response = supabase.table("tasks") \
            .select("*") \
            .eq("id", str(task_id)) \
            .execute()
        
        # Check if task exists
        if not response.data:
            raise HTTPException(status_code=404, detail="Task not found")
        
        task = response.data[0]
        
        # Check if the task belongs to the authenticated user
        if task["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this task")
        
        # Return the task
        return task
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log the error
        print(f"Error fetching task: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch task")

@router.post("/", response_model=TaskResponse, status_code=201, responses={
    401: {"model": ErrorResponse},
    422: {"model": ErrorResponse}
})
async def create_task(
    task: TaskCreate,
    user_id: str = Depends(get_user_from_header),
    supabase = Depends(get_supabase_client)
):
    """
    Create a new task
    
    This endpoint demonstrates:
    - Request body validation with Pydantic
    - Creating resources in the database
    - Returning the created resource
    """
    try:
        # Get the highest order_position
        response = supabase.table("tasks") \
            .select("order_position") \
            .eq("user_id", user_id) \
            .order("order_position", {"ascending": False}) \
            .limit(1) \
            .execute()
        
        new_position = 1
        if response.data:
            new_position = response.data[0]["order_position"] + 1
        
        # Prepare task data
        now = datetime.utcnow().isoformat()
        task_data = {
            "title": task.title,
            "description": task.description or "",
            "completed": False,
            "order_position": new_position,
            "user_id": user_id,
            "created_at": now,
            "updated_at": now,
            "priority": task.priority,
            "tags": task.tags,
            "due_date": task.due_date.isoformat() if task.due_date else None
        }
        
        # Create the task in Supabase
        response = supabase.table("tasks") \
            .insert(task_data) \
            .execute()
        
        # Return the created task
        return response.data[0]
    except Exception as e:
        # Log the error
        print(f"Error creating task: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create task")

@router.patch("/{task_id}", response_model=TaskResponse, responses={
    401: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
    422: {"model": ErrorResponse}
})
async def update_task(
    task_id: UUID,
    task_update: TaskUpdate,
    user_id: str = Depends(get_user_from_header),
    supabase = Depends(get_supabase_client)
):
    """
    Update an existing task
    
    This endpoint demonstrates:
    - Partial updates with Pydantic
    - Complex business logic
    - Conditional updates
    """
    try:
        # First, check if the task exists and belongs to the user
        response = supabase.table("tasks") \
            .select("*") \
            .eq("id", str(task_id)) \
            .execute()
        
        # Check if task exists
        if not response.data:
            raise HTTPException(status_code=404, detail="Task not found")
        
        existing_task = response.data[0]
        
        # Check if the task belongs to the authenticated user
        if existing_task["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this task")
        
        # Prepare update data
        update_data = {}
        
        # Only include fields that are provided in the request
        if task_update.title is not None:
            update_data["title"] = task_update.title
        
        if task_update.description is not None:
            update_data["description"] = task_update.description
        
        if task_update.priority is not None:
            update_data["priority"] = task_update.priority
        
        if task_update.tags is not None:
            update_data["tags"] = task_update.tags
        
        if task_update.due_date is not None:
            update_data["due_date"] = task_update.due_date.isoformat()
        
        if task_update.completed is not None:
            update_data["completed"] = task_update.completed
            
            # Update completed_at timestamp if task is being marked as completed
            if task_update.completed and not existing_task["completed"]:
                update_data["completed_at"] = datetime.utcnow().isoformat()
            
            # Clear completed_at if task is being marked as not completed
            if not task_update.completed and existing_task["completed"]:
                update_data["completed_at"] = None
        
        # Always update the updated_at timestamp
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        # Update the task in Supabase
        response = supabase.table("tasks") \
            .update(update_data) \
            .eq("id", str(task_id)) \
            .execute()
        
        # Return the updated task
        return response.data[0]
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log the error
        print(f"Error updating task: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update task")

@router.delete("/{task_id}", response_model=Dict[str, Any], responses={
    401: {"model": ErrorResponse},
    404: {"model": ErrorResponse}
})
async def delete_task(
    task_id: UUID,
    user_id: str = Depends(get_user_from_header),
    supabase = Depends(get_supabase_client)
):
    """
    Delete a task
    
    This endpoint demonstrates:
    - Resource deletion
    - Security checks
    - Success responses
    """
    try:
        # First, check if the task exists and belongs to the user
        response = supabase.table("tasks") \
            .select("*") \
            .eq("id", str(task_id)) \
            .execute()
        
        # Check if task exists
        if not response.data:
            raise HTTPException(status_code=404, detail="Task not found")
        
        task = response.data[0]
        
        # Check if the task belongs to the authenticated user
        if task["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this task")
        
        # Delete the task
        supabase.table("tasks") \
            .delete() \
            .eq("id", str(task_id)) \
            .execute()
        
        # Return success
        return {"success": True, "id": str(task_id)}
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log the error
        print(f"Error deleting task: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete task")

@router.get("/analytics/summary", response_model=TaskAnalytics, responses={
    401: {"model": ErrorResponse}
})
async def get_task_analytics(
    user_id: str = Depends(get_user_from_header),
    supabase = Depends(get_supabase_client)
):
    """
    Get analytics for the user's tasks
    
    This endpoint demonstrates:
    - Complex data processing
    - Aggregation and statistics
    - Business intelligence features
    """
    try:
        # Get all tasks for the user
        response = supabase.table("tasks") \
            .select("*") \
            .eq("user_id", user_id) \
            .execute()
        
        tasks = response.data
        
        # Calculate analytics
        total_tasks = len(tasks)
        completed_tasks = sum(1 for task in tasks if task["completed"])
        
        # Avoid division by zero
        completion_rate = (completed_tasks / total_tasks) if total_tasks > 0 else 0
        
        # Calculate average completion time for completed tasks
        completion_times = []
        for task in tasks:
            if task["completed"] and task["completed_at"]:
                created = datetime.fromisoformat(task["created_at"].replace("Z", "+00:00"))
                completed = datetime.fromisoformat(task["completed_at"].replace("Z", "+00:00"))
                completion_time = (completed - created).total_seconds() / 3600  # hours
                completion_times.append(completion_time)
        
        average_completion_time = sum(completion_times) / len(completion_times) if completion_times else None
        
        # Count tasks by priority
        tasks_by_priority = {
            "none": 0,
            "low": 0,
            "medium": 0,
            "high": 0
        }
        
        for task in tasks:
            priority = task["priority"] or "none"
            tasks_by_priority[priority] += 1
        
        # Count tasks by tag
        tasks_by_tag = {}
        for task in tasks:
            if task["tags"]:
                for tag in task["tags"]:
                    if tag in tasks_by_tag:
                        tasks_by_tag[tag] += 1
                    else:
                        tasks_by_tag[tag] = 1
        
        # Count overdue tasks
        now = datetime.utcnow()
        overdue_tasks = sum(
            1 for task in tasks 
            if not task["completed"] and task["due_date"] 
            and datetime.fromisoformat(task["due_date"].replace("Z", "+00:00")) < now
        )
        
        # Return analytics
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "completion_rate": completion_rate,
            "average_completion_time": average_completion_time,
            "tasks_by_priority": tasks_by_priority,
            "tasks_by_tag": tasks_by_tag,
            "overdue_tasks": overdue_tasks
        }
    except Exception as e:
        # Log the error
        print(f"Error generating task analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate task analytics")

@router.post("/ai-enhance", response_model=TaskResponse, responses={
    401: {"model": ErrorResponse},
    404: {"model": ErrorResponse}
})
async def enhance_task_with_ai(
    task_id: UUID,
    user_id: str = Depends(get_user_from_header),
    supabase = Depends(get_supabase_client)
):
    """
    Enhance a task using AI
    
    This endpoint demonstrates:
    - Integration with AI services
    - Complex business logic that's better suited for the backend
    - Processing that would be inefficient in the frontend
    """
    try:
        # First, check if the task exists and belongs to the user
        response = supabase.table("tasks") \
            .select("*") \
            .eq("id", str(task_id)) \
            .execute()
        
        # Check if task exists
        if not response.data:
            raise HTTPException(status_code=404, detail="Task not found")
        
        task = response.data[0]
        
        # Check if the task belongs to the authenticated user
        if task["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to enhance this task")
        
        # In a real application, this would call an AI service
        # For this example, we'll just add some tags and improve the description
        
        # Simulate AI processing
        enhanced_description = task["description"]
        if enhanced_description:
            enhanced_description += "\n\nAI-enhanced: This task has been prioritized based on your work patterns."
        else:
            enhanced_description = "AI-enhanced: This task has been prioritized based on your work patterns."
        
        # Add AI-suggested tags
        tags = task["tags"] or []
        if "ai-enhanced" not in tags:
            tags.append("ai-enhanced")
        
        # Update the task with AI enhancements
        update_data = {
            "description": enhanced_description,
            "tags": tags,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Update the task in Supabase
        response = supabase.table("tasks") \
            .update(update_data) \
            .eq("id", str(task_id)) \
            .execute()
        
        # Return the enhanced task
        return response.data[0]
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log the error
        print(f"Error enhancing task with AI: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to enhance task with AI")