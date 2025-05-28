from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.schemas import TaskCreate, TaskUpdate, TaskResponse
from app.services.task_service import TaskService

router = APIRouter()

@router.get("/", response_model=List[TaskResponse])
def get_tasks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all tasks"""
    tasks = TaskService.get_tasks(db, skip=skip, limit=limit)
    return tasks

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task"""
    return TaskService.create_task(db, task)

@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """Get a specific task by ID"""
    task = TaskService.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.put("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task: TaskUpdate, db: Session = Depends(get_db)):
    """Update a task"""
    updated_task = TaskService.update_task(db, task_id, task)
    if not updated_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated_task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Delete a task"""
    success = TaskService.delete_task(db, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return None

@router.put("/reorder", response_model=List[TaskResponse])
def reorder_tasks(task_ids: List[int], db: Session = Depends(get_db)):
    """Reorder tasks based on the provided list of task IDs"""
    return TaskService.reorder_tasks(db, task_ids)
