from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.session import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    tasks = relationship("Task", back_populates="user")
    
class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    completed = Column(Boolean, default=False, nullable=False)
    order_position = Column(Integer, nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    user = relationship("User", back_populates="tasks")
    
class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    meta_data = Column(JSON)  # Changed from 'metadata' to 'meta_data' to avoid reserved name
    domain = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
class TALBlock(Base):
    __tablename__ = "tal_blocks"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    content = Column(Text)
    block_type = Column(String, index=True)
    meta_data = Column(JSON)  # Changed from 'metadata' to 'meta_data' to avoid reserved name
    created_at = Column(DateTime, default=datetime.utcnow)
    
class Debate(Base):
    __tablename__ = "debates"
    
    id = Column(Integer, primary_key=True, index=True)
    topic = Column(Text)
    summary = Column(Text)
    experts = Column(JSON)
    rounds = Column(Integer)
    result = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
