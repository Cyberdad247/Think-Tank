from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc

from app.models.task import Task
from app.models.schemas import TaskCreate, TaskUpdate

class TaskService:
    @staticmethod
    def get_tasks(db: Session, skip: int = 0, limit: int = 100) -> List[Task]:
        """Get all tasks ordered by order_position"""
        return db.query(Task).order_by(Task.order_position).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_task(db: Session, task_id: int) -> Optional[Task]:
        """Get a specific task by ID"""
        return db.query(Task).filter(Task.id == task_id).first()
    
    @staticmethod
    def create_task(db: Session, task_create: TaskCreate) -> Task:
        """Create a new task"""
        # Get the highest order_position and add 1
        highest_position = db.query(Task).order_by(desc(Task.order_position)).first()
        new_position = 1 if not highest_position else highest_position.order_position + 1
        
        # Create new task
        db_task = Task(
            title=task_create.title,
            description=task_create.description,
            completed=task_create.completed,
            order_position=new_position
        )
        
        # Add to database
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        
        return db_task
    
    @staticmethod
    def update_task(db: Session, task_id: int, task_update: TaskUpdate) -> Optional[Task]:
        """Update an existing task"""
        db_task = TaskService.get_task(db, task_id)
        
        if not db_task:
            return None
        
        # Update task fields if provided
        update_data = task_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_task, key, value)
        
        db.commit()
        db.refresh(db_task)
        
        return db_task
    
    @staticmethod
    def delete_task(db: Session, task_id: int) -> bool:
        """Delete a task"""
        db_task = TaskService.get_task(db, task_id)
        
        if not db_task:
            return False
        
        db.delete(db_task)
        db.commit()
        
        return True
    
    @staticmethod
    def reorder_tasks(db: Session, task_ids: List[int]) -> List[Task]:
        """Reorder tasks based on the provided list of task IDs"""
        # Get all tasks
        tasks = db.query(Task).all()
        task_dict = {task.id: task for task in tasks}
        
        # Update order_position for each task
        for index, task_id in enumerate(task_ids, start=1):
            if task_id in task_dict:
                task_dict[task_id].order_position = index
        
        db.commit()
        
        # Return tasks in new order
        return db.query(Task).order_by(Task.order_position).all()
