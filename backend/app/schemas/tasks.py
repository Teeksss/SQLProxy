"""
Tasks schemas for SQL Proxy

This module provides Pydantic schemas for validating and serializing
scheduled tasks and jobs data.

Last updated: 2025-05-21 05:32:06
Updated by: Teeksss
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime

class TaskCreate(BaseModel):
    """Schema for creating a scheduled task"""
    task_id: str = Field(..., description="Unique task identifier")
    task_type: str = Field(..., description="Task type (backup, metrics_export, metrics_reset, backup_cleanup)")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Task parameters")
    interval_hours: Optional[float] = Field(None, description="Run task every X hours")
    interval_minutes: Optional[float] = Field(None, description="Run task every X minutes")
    interval_seconds: Optional[float] = Field(None, description="Run task every X seconds")
    first_run: Optional[str] = Field(None, description="When to run the task first (ISO format)")
    run_at: Optional[str] = Field(None, description="Time to run the task daily (HH:MM)")
    run_daily: bool = Field(False, description="Whether to run the task daily")
    
    @validator('task_id')
    def task_id_must_be_valid(cls, v):
        if not v or ' ' in v:
            raise ValueError('Task ID must not be empty or contain spaces')
        return v
    
    @validator('task_type')
    def task_type_must_be_valid(cls, v):
        valid_types = ["backup", "metrics_export", "metrics_reset", "backup_cleanup"]
        if v not in valid_types:
            raise ValueError(f'Task type must be one of: {", ".join(valid_types)}')
        return v
    
    @validator('first_run')
    def first_run_must_be_valid(cls, v):
        if v:
            try:
                datetime.fromisoformat(v)
            except ValueError:
                raise ValueError('First run must be a valid ISO format datetime')
        return v
    
    @validator('run_at')
    def run_at_must_be_valid(cls, v):
        if v:
            try:
                hours, minutes = map(int, v.split(':'))
                if hours < 0 or hours > 23 or minutes < 0 or minutes > 59:
                    raise ValueError()
            except:
                raise ValueError('Run at must be in format HH:MM (24-hour)')
        return v
    
    @validator('interval_hours', 'interval_minutes', 'interval_seconds')
    def intervals_must_be_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Interval must be positive')
        return v
    
    @validator('parameters')
    def parameters_must_be_valid(cls, v, values):
        task_type = values.get('task_type')
        
        if task_type == 'backup':
            if 'backup_type' in v and v['backup_type'] not in ['full', 'incremental']:
                raise ValueError('Backup type must be full or incremental')
        
        return v

class TaskBase(BaseModel):
    """Base schema for task information"""
    id: str = Field(..., description="Task identifier")
    next_run: Optional[str] = Field(None, description="Next scheduled run time")
    last_run: Optional[str] = Field(None, description="Last run time")
    interval: Optional[str] = Field(None, description="Task interval")
    tags: List[str] = Field(default_factory=list, description="Task tags")

class TaskResponse(BaseModel):
    """Schema for task response"""
    task: TaskBase = Field(..., description="Task information")

class TaskListResponse(BaseModel):
    """Schema for task list response"""
    tasks: List[TaskBase] = Field(..., description="List of tasks")

# Son güncelleme: 2025-05-21 05:32:06
# Güncelleyen: Teeksss