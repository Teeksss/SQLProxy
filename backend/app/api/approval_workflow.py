"""
Multi-step approval workflow endpoints for SQL Proxy.

Provides functionality for configuring and executing multi-step approval workflows
for high-risk or sensitive SQL queries.

Last updated: 2025-05-20 06:11:09
Updated by: Teeksss
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body, Path, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from app.db.session import get_db
from app.auth.jwt import get_current_user, TokenData
from app.models.approval import ApprovalWorkflow, ApprovalStep, ApprovalInstance, StepInstance
from app.models.query import PendingApproval, AuditLog
from app.models.server import ServerConfig
from app.services.notification_service import notification_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/workflows", response_model=List[Dict[str, Any]])
async def get_approval_workflows(
    status: Optional[str] = Query(None, description="Filter by status (active/inactive)"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all approval workflows
    
    Returns a list of configured approval workflows
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can view approval workflows"
        )
    
    # Build query
    query = db.query(ApprovalWorkflow)
    
    # Apply filters
    if status == "active":
        query = query.filter(ApprovalWorkflow.is_active == True)
    elif status == "inactive":
        query = query.filter(ApprovalWorkflow.is_active == False)
    
    # Execute query
    workflows = query.order_by(ApprovalWorkflow.priority.desc()).all()
    
    # Format result
    result = []
    for workflow in workflows:
        # Get steps for this workflow
        steps = db.query(ApprovalStep).filter(
            ApprovalStep.workflow_id == workflow.id
        ).order_by(ApprovalStep.step_order).all()
        
        workflow_data = {
            "id": workflow.id,
            "name": workflow.name,
            "description": workflow.description,
            "rule_type": workflow.rule_type,
            "rule_condition": workflow.rule_condition,
            "priority": workflow.priority,
            "is_active": workflow.is_active,
            "created_by": workflow.created_by,
            "created_at": workflow.created_at.isoformat(),
            "steps": [
                {
                    "id": step.id,
                    "name": step.name,
                    "description": step.description,
                    "approver_type": step.approver_type,
                    "approver_value": step.approver_value,
                    "step_order": step.step_order,
                    "is_required": step.is_required
                }
                for step in steps
            ]
        }
        
        result.append(workflow_data)
    
    return result

@router.post("/workflows", response_model=Dict[str, Any])
async def create_approval_workflow(
    data: Dict[str, Any] = Body(...),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new approval workflow
    
    Creates a multi-step approval workflow for SQL queries
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can create approval workflows"
        )
    
    # Validate request data
    required_fields = ["name", "rule_type", "rule_condition", "steps"]
    for field in required_fields:
        if field not in data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required field: {field}"
            )
    
    # Validate workflow steps
    steps = data.get("steps", [])
    if not steps:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one approval step is required"
        )
    
    for step in steps:
        if "name" not in step or "approver_type" not in step or "approver_value" not in step:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Each step must have name, approver_type, and approver_value"
            )
    
    # Create workflow
    workflow = ApprovalWorkflow(
        name=data["name"],
        description=data.get("description", ""),
        rule_type=data["rule_type"],
        rule_condition=data["rule_condition"],
        priority=data.get("priority", 10),
        is_active=data.get("is_active", True),
        created_by=current_user.username
    )
    
    db.add(workflow)
    db.flush()  # Get workflow ID but don't commit yet
    
    # Create steps
    for i, step_data in enumerate(steps):
        step = ApprovalStep(
            workflow_id=workflow.id,
            name=step_data["name"],
            description=step_data.get("description", ""),
            approver_type=step_data["approver_type"],
            approver_value=step_data["approver_value"],
            step_order=step_data.get("step_order", i + 1),
            is_required=step_data.get("is_required", True)
        )
        db.add(step)
    
    # Commit all changes
    db.commit()
    db.refresh(workflow)
    
    # Get steps for response
    workflow_steps = db.query(ApprovalStep).filter(
        ApprovalStep.workflow_id == workflow.id
    ).order_by(ApprovalStep.step_order).all()
    
    return {
        "id": workflow.id,
        "name": workflow.name,
        "description": workflow.description,
        "rule_type": workflow.rule_type,
        "rule_condition": workflow.rule_condition,
        "priority": workflow.priority,
        "is_active": workflow.is_active,
        "created_by": workflow.created_by,
        "created_at": workflow.created_at.isoformat(),
        "steps": [
            {
                "id": step.id,
                "name": step.name,
                "description": step.description,
                "approver_type": step.approver_type,
                "approver_value": step.approver_value,
                "step_order": step.step_order,
                "is_required": step.is_required
            }
            for step in workflow_steps
        ]
    }

@router.put("/workflows/{workflow_id}", response_model=Dict[str, Any])
async def update_approval_workflow(
    workflow_id: int = Path(..., title="Workflow ID"),
    data: Dict[str, Any] = Body(...),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing approval workflow
    
    Updates an approval workflow and its steps
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can update approval workflows"
        )
    
    # Find workflow
    workflow = db.query(ApprovalWorkflow).filter(
        ApprovalWorkflow.id == workflow_id
    ).first()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval workflow with ID {workflow_id} not found"
        )
    
    # Update workflow fields
    if "name" in data:
        workflow.name = data["name"]
    
    if "description" in data:
        workflow.description = data["description"]
    
    if "rule_type" in data:
        workflow.rule_type = data["rule_type"]
    
    if "rule_condition" in data:
        workflow.rule_condition = data["rule_condition"]
    
    if "priority" in data:
        workflow.priority = data["priority"]
    
    if "is_active" in data:
        workflow.is_active = data["is_active"]
    
    # Update steps if provided
    if "steps" in data:
        steps = data["steps"]
        
        # Delete existing steps
        db.query(ApprovalStep).filter(
            ApprovalStep.workflow_id == workflow_id
        ).delete()
        
        # Create new steps
        for i, step_data in enumerate(steps):
            step = ApprovalStep(
                workflow_id=workflow.id,
                name=step_data["name"],
                description=step_data.get("description", ""),
                approver_type=step_data["approver_type"],
                approver_value=step_data["approver_value"],
                step_order=step_data.get("step_order", i + 1),
                is_required=step_data.get("is_required", True)
            )
            db.add(step)
    
    # Update audit fields
    workflow.updated_by = current_user.username
    workflow.updated_at = datetime.utcnow()
    
    # Commit changes
    db.commit()
    db.refresh(workflow)
    
    # Get updated steps
    workflow_steps = db.query(ApprovalStep).filter(
        ApprovalStep.workflow_id == workflow.id
    ).order_by(ApprovalStep.step_order).all()
    
    return {
        "id": workflow.id,
        "name": workflow.name,
        "description": workflow.description,
        "rule_type": workflow.rule_type,
        "rule_condition": workflow.rule_condition,
        "priority": workflow.priority,
        "is_active": workflow.is_active,
        "created_by": workflow.created_by,
        "created_at": workflow.created_at.isoformat(),
        "updated_by": workflow.updated_by,
        "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None,
        "steps": [
            {
                "id": step.id,
                "name": step.name,
                "description": step.description,
                "approver_type": step.approver_type,
                "approver_value": step.approver_value,
                "step_order": step.step_order,
                "is_required": step.is_required
            }
            for step in workflow_steps
        ]
    }

@router.delete("/workflows/{workflow_id}", response_model=Dict[str, Any])
async def delete_approval_workflow(
    workflow_id: int = Path(..., title="Workflow ID"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an approval workflow
    
    Deletes an approval workflow and all its steps
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can delete approval workflows"
        )
    
    # Find workflow
    workflow = db.query(ApprovalWorkflow).filter(
        ApprovalWorkflow.id == workflow_id
    ).first()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval workflow with ID {workflow_id} not found"
        )
    
    # Check if there are active approval instances using this workflow
    active_instances = db.query(ApprovalInstance).filter(
        ApprovalInstance.workflow_id == workflow_id,
        ApprovalInstance.status.in_(["pending", "in_progress"])
    ).count()
    
    if active_instances > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete workflow with {active_instances} active approval instances"
        )
    
    # Delete steps
    db.query(ApprovalStep).filter(
        ApprovalStep.workflow_id == workflow_id
    ).delete()
    
    # Delete workflow
    db.delete(workflow)
    db.commit()
    
    return {
        "message": f"Approval workflow with ID {workflow_id} has been deleted"
    }

@router.get("/instances", response_model=List[Dict[str, Any]])
async def get_approval_instances(
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get approval workflow instances
    
    Returns a list of approval workflow instances based on filters
    """
    if current_user.role != "admin":
        # For non-admin users, only show instances where they are an approver
        query = db.query(ApprovalInstance).join(
            StepInstance,
            StepInstance.instance_id == ApprovalInstance.id
        ).filter(
            StepInstance.approver_value.contains(current_user.username)
        )
    else:
        # Admin users can see all instances
        query = db.query(ApprovalInstance)
    
    # Apply status filter
    if status:
        query = query.filter(ApprovalInstance.status == status)
    
    # Get instances
    instances = query.order_by(ApprovalInstance.created_at.desc()).all()
    
    # Format result
    result = []
    for instance in instances:
        # Get steps for this instance
        steps = db.query(StepInstance).filter(
            StepInstance.instance_id == instance.id
        ).order_by(StepInstance.step_order).all()
        
        # Get query information
        pending_approval = db.query(PendingApproval).filter(
            PendingApproval.id == instance.query_id
        ).first()
        
        instance_data = {
            "id": instance.id,
            "workflow_id": instance.workflow_id,
            "workflow_name": instance.workflow_name,
            "query_id": instance.query_id,
            "current_step": instance.current_step,
            "status": instance.status,
            "created_at": instance.created_at.isoformat(),
            "updated_at": instance.updated_at.isoformat() if instance.updated_at else None,
            "submitted_by": pending_approval.username if pending_approval else "Unknown",
            "sql_query": pending_approval.query_text if pending_approval else "Query not found",
            "target_server": pending_approval.target_server if pending_approval else "Unknown",
            "steps": [
                {
                    "id": step.id,
                    "name": step.step_name,
                    "approver_type": step.approver_type,
                    "approver_value": step.approver_value,
                    "status": step.status,
                    "step_order": step.step_order,
                    "approver_comment": step.approver_comment,
                    "approved_by": step.approved_by,
                    "approved_at": step.approved_at.isoformat() if step.approved_at else None,
                    "is_required": step.is_required
                }
                for step in steps
            ]
        }
        
        result.append(instance_data)
    
    return result

@router.get("/instances/{instance_id}", response_model=Dict[str, Any])
async def get_approval_instance(
    instance_id: int = Path(..., title="Instance ID"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get details for a specific approval instance
    
    Returns details about an approval workflow instance and its steps
    """
    # Find the instance
    instance = db.query(ApprovalInstance).filter(
        ApprovalInstance.id == instance_id
    ).first()
    
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval instance with ID {instance_id} not found"
        )
    
    # Check permissions
    if current_user.role != "admin":
        # Check if user is an approver for any step
        is_approver = db.query(StepInstance).filter(
            StepInstance.instance_id == instance_id,
            StepInstance.approver_value.contains(current_user.username)
        ).count() > 0
        
        # Check if user is the query submitter
        pending_approval = db.query(PendingApproval).filter(
            PendingApproval.id == instance.query_id
        ).first()
        
        is_submitter = pending_approval and pending_approval.username == current_user.username
        
        if not is_approver and not is_submitter:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this approval instance"
            )
    
    # Get steps for this instance
    steps = db.query(StepInstance).filter(
        StepInstance.instance_id == instance.id
    ).order_by(StepInstance.step_order).all()
    
    # Get query information
    pending_approval = db.query(PendingApproval).filter(
        PendingApproval.id == instance.query_id
    ).first()
    
    # Get the workflow
    workflow = db.query(ApprovalWorkflow).filter(
        ApprovalWorkflow.id == instance.workflow_id
    ).first()
    
    # Format result
    result = {
        "id": instance.id,
        "workflow_id": instance.workflow_id,
        "workflow_name": instance.workflow_name,
        "workflow_description": workflow.description if workflow else None,
        "query_id": instance.query_id,
        "current_step": instance.current_step,
        "status": instance.status,
        "created_at": instance.created_at.isoformat(),
        "updated_at": instance.updated_at.isoformat() if instance.updated_at else None,
        "query_details": {
            "submitted_by": pending_approval.username if pending_approval else "Unknown",
            "submitted_at": pending_approval.created_at.isoformat() if pending_approval else None,
            "sql_query": pending_approval.query_text if pending_approval else "Query not found",
            "target_server": pending_approval.target_server if pending_approval else "Unknown",
            "justification": pending_approval.justification if pending_approval else None
        },
        "steps": [
            {
                "id": step.id,
                "name": step.step_name,
                "description": step.step_description,
                "approver_type": step.approver_type,
                "approver_value": step.approver_value,
                "status": step.status,
                "step_order": step.step_order,
                "approver_comment": step.approver_comment,
                "approved_by": step.approved_by,
                "approved_at": step.approved_at.isoformat() if step.approved_at else None,
                "is_current": instance.current_step == step.step_order,
                "is_required": step.is_required
            }
            for step in steps
        ]
    }
    
    return result

@router.post("/instances/{instance_id}/steps/{step_id}/approve", response_model=Dict[str, Any])
async def approve_step(
    instance_id: int = Path(..., title="Instance ID"),
    step_id: int = Path(..., title="Step ID"),
    data: Dict[str, Any] = Body(...),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Approve a step in an approval workflow instance
    
    Marks a step as approved and advances the workflow if appropriate
    """
    # Find the instance
    instance = db.query(ApprovalInstance).filter(
        ApprovalInstance.id == instance_id
    ).first()
    
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval instance with ID {instance_id} not found"
        )
    
    # Find the step
    step = db.query(StepInstance).filter(
        StepInstance.id == step_id,
        StepInstance.instance_id == instance_id
    ).first()
    
    if not step:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Step with ID {step_id} not found in instance {instance_id}"
        )
    
    # Check if this is the current step
    if instance.current_step != step.step_order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve step {step_id} as it is not the current step"
        )
    
    # Check if instance is in a state that can be approved
    if instance.status not in ["pending", "in_progress"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve step in instance with status {instance.status}"
        )
    
    # Check if user has permission to approve this step
    if current_user.role != "admin":
        # Check approver type
        if step.approver_type == "user" and current_user.username not in step.approver_value.split(","):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to approve this step"
            )
        elif step.approver_type == "role" and current_user.role not in step.approver_value.split(","):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your role doesn't have permission to approve this step"
            )
    
    # Update step status
    step.status = "approved"
    step.approver_comment = data.get("comment", "")
    step.approved_by = current_user.username
    step.approved_at = datetime.utcnow()
    
    # Update instance status
    # If this is the first step, update status to in_progress
    if instance.status == "pending":
        instance.status = "in_progress"
    
    # Find the next step
    next_step = db.query(StepInstance).filter(
        StepInstance.instance_id == instance_id,
        StepInstance.step_order > step.step_order
    ).order_by(StepInstance.step_order).first()
    
    if next_step:
        # Move to the next step
        instance.current_step = next_step.step_order
        
        # Send notification to the next approver
        try:
            approvers = next_step.approver_value.split(",")
            for approver in approvers:
                notification_title = f"Approval Required: {instance.workflow_name}"
                notification_message = f"Your approval is required for step '{next_step.step_name}' in the approval workflow for a query."
                
                await notification_service.send_user_notification(
                    approver.strip(), 
                    notification_title, 
                    notification_message, 
                    link=f"/admin/approval-workflows/instances/{instance_id}"
                )
        except Exception as e:
            logger.error(f"Error sending notification to next approver: {str(e)}")
    else:
        # No more steps, workflow is complete
        instance.status = "approved"
        
        # Get the pending approval and update its status
        pending_approval = db.query(PendingApproval).filter(
            PendingApproval.id == instance.query_id
        ).first()
        
        if pending_approval:
            pending_approval.status = "approved"
            pending_approval.approved_by = current_user.username
            pending_approval.approved_at = datetime.utcnow()
            pending_approval.approver_comment = "Approved through multi-step workflow"
            
            # Send notification to the submitter
            try:
                notification_title = "Query Approval Complete"
                notification_message = f"Your query has been approved through the multi-step workflow: {instance.workflow_name}"
                
                await notification_service.send_user_notification(
                    pending_approval.username,
                    notification_title,
                    notification_message,
                    link=f"/dashboard/queries/{pending_approval.id}"
                )
            except Exception as e:
                logger.error(f"Error sending notification to query submitter: {str(e)}")
    
    # Update instance
    instance.updated_at = datetime.utcnow()
    
    # Commit changes
    db.commit()
    
    return {
        "message": "Step approved successfully",
        "instance_id": instance.id,
        "step_id": step.id,
        "new_status": instance.status,
        "current_step": instance.current_step
    }

@router.post("/instances/{instance_id}/steps/{step_id}/reject", response_model=Dict[str, Any])
async def reject_step(
    instance_id: int = Path(..., title="Instance ID"),
    step_id: int = Path(..., title="Step ID"),
    data: Dict[str, Any] = Body(...),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reject a step in an approval workflow instance
    
    Marks a step as rejected and ends the workflow
    """
    # Find the instance
    instance = db.query(ApprovalInstance).filter(
        ApprovalInstance.id == instance_id
    ).first()
    
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval instance with ID {instance_id} not found"
        )
    
    # Find the step
    step = db.query(StepInstance).filter(
        StepInstance.id == step_id,
        StepInstance.instance_id == instance_id
    ).first()
    
    if not step:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Step with ID {step_id} not found in instance {instance_id}"
        )
    
    # Check if this is the current step
    if instance.current_step != step.step_order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reject step {step_id} as it is not the current step"
        )
    
    # Check if instance is in a state that can be rejected
    if instance.status not in ["pending", "in_progress"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reject step in instance with status {instance.status}"
        )
    
    # Ensure rejection reason is provided
    if "comment" not in data or not data["comment"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rejection reason is required"
        )
    
    # Check if user has permission to reject this step
    if current_user.role != "admin":
        # Check approver type
        if step.approver_type == "user" and current_user.username not in step.approver_value.split(","):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to reject this step"
            )
        elif step.approver_type == "role" and current_user.role not in step.approver_value.split(","):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your role doesn't have permission to reject this step"
            )
    
    # Update step status
    step.status = "rejected"
    step.approver_comment = data["comment"]
    step.approved_by = current_user.username
    step.approved_at = datetime.utcnow()
    
    # Update instance status
    instance.status = "rejected"
    instance.updated_at = datetime.utcnow()
    
    # Get the pending approval and update its status
    pending_approval = db.query(PendingApproval).filter(
        PendingApproval.id == instance.query_id
    ).first()
    
    if pending_approval:
        pending_approval.status = "rejected"
        pending_approval.rejected_by = current_user.username
        pending_approval.rejected_at = datetime.utcnow()
        pending_approval.rejection_reason = data["comment"]
        
        # Send notification to the submitter
        try:
            notification_title = "Query Rejected"
            notification_message = f"Your query has been rejected at step '{step.step_name}' in the workflow: {instance.workflow_name}"
            notification_message += f"\n\nReason: {data['comment']}"
            
            await notification_service.send_user_notification(
                pending_approval.username,
                notification_title,
                notification_message,
                link=f"/dashboard/queries/{pending_approval.id}"
            )
        except Exception as e:
            logger.error(f"Error sending notification to query submitter: {str(e)}")
    
    # Commit changes
    db.commit()
    
    return {
        "message": "Step rejected successfully",
        "instance_id": instance.id,
        "step_id": step.id,
        "new_status": instance.status
    }

# Test endpoints for workflow rule evaluation - admin only

@router.post("/evaluate-rule", response_model=Dict[str, Any])
async def evaluate_workflow_rule(
    data: Dict[str, Any] = Body(...),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Test evaluation of a workflow rule against a query
    
    Used for testing workflow rules without creating actual instances
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can use this endpoint"
        )
    
    # Validate request data
    required_fields = ["rule_type", "rule_condition", "sql_query"]
    for field in required_fields:
        if field not in data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required field: {field}"
            )
    
    from app.services.workflow_service import WorkflowService
    
    # Create workflow service
    workflow_service = WorkflowService(db)
    
    # Evaluate rule
    result = workflow_service.evaluate_rule(
        data["rule_type"],
        data["rule_condition"],
        data["sql_query"],
        data.get("server_alias", ""),
        data.get("username", "")
    )
    
    return {
        "matches": result,
        "rule_type": data["rule_type"],
        "rule_condition": data["rule_condition"],
        "sql_query": data["sql_query"][:100] + ("..." if len(data["sql_query"]) > 100 else "")
    }

# Son güncelleme: 2025-05-20 06:11:09
# Güncelleyen: Teeksss