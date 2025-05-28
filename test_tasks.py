import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import get_db
from app.models.task import Task
from main import app

# Create a separate Base for testing to avoid metadata conflicts
TestBase = declarative_base()

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Define test models directly to avoid importing conflicts
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from datetime import datetime

class TestTask(TestBase):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    completed = Column(Boolean, default=False, nullable=False)
    order_position = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

# Override the get_db dependency
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)

@pytest.fixture(scope="function")
def test_db():
    # Create the database tables
    TestBase.metadata.create_all(bind=engine)
    
    # Add test data
    db = TestingSessionLocal()
    
    # Add tasks
    db.add(TestTask(title="Test task 1", description="Description 1", completed=False, order_position=1))
    db.add(TestTask(title="Test task 2", description="Description 2", completed=True, order_position=2))
    db.commit()
    
    yield
    
    # Drop the tables after the test
    TestBase.metadata.drop_all(bind=engine)

def test_get_tasks(test_db):
    response = client.get("/api/tasks/")
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 2
    assert tasks[0]["title"] == "Test task 1"
    assert tasks[1]["title"] == "Test task 2"

def test_create_task(test_db):
    response = client.post(
        "/api/tasks/",
        json={"title": "New test task", "description": "New description", "completed": False}
    )
    assert response.status_code == 201
    task = response.json()
    assert task["title"] == "New test task"
    assert task["description"] == "New description"
    assert task["completed"] == False
    assert task["order_position"] == 3

def test_update_task(test_db):
    # First get the tasks to find the ID
    response = client.get("/api/tasks/")
    tasks = response.json()
    task_id = tasks[0]["id"]
    
    # Update the task
    response = client.put(
        f"/api/tasks/{task_id}",
        json={"title": "Updated task", "completed": True}
    )
    assert response.status_code == 200
    task = response.json()
    assert task["title"] == "Updated task"
    assert task["completed"] == True

def test_delete_task(test_db):
    # First get the tasks to find the ID
    response = client.get("/api/tasks/")
    tasks = response.json()
    task_id = tasks[0]["id"]
    
    # Delete the task
    response = client.delete(f"/api/tasks/{task_id}")
    assert response.status_code == 204
    
    # Verify it's deleted
    response = client.get("/api/tasks/")
    tasks = response.json()
    assert len(tasks) == 1
