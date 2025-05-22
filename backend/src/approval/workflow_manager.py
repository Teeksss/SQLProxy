from typing import Dict, List, Optional
from datetime import datetime
import asyncio
from .notifier import ApprovalNotifier
from .audit_logger import AuditLogger

class ApprovalWorkflow:
    def __init__(self):
        self.notifier = ApprovalNotifier()
        self.audit = AuditLogger()
        
    async def submit_for_approval(self, query: str,
                                analysis: Dict,
                                submitter: str) -> Dict:
        """Query'yi onay workflow'una sokar."""
        # Create approval request
        request = {
            'id': self._generate_request_id(),
            'query': query,
            'analysis': analysis,
            'submitter': submitter,
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat(),
            'approvers': await self._determine_approvers(analysis)
        }
        
        # Save request
        await self._save_request(request)
        
        # Notify approvers
        await self.notifier.notify_approvers(
            request_id=request['id'],
            approvers=request['approvers'],
            analysis=analysis
        )
        
        return request
        
    async def process_approval(self, request_id: str,
                             approver: str,
                             decision: str,
                             comments: str = None) -> Dict:
        """Onay kararını işler."""
        request = await self._get_request(request_id)
        
        if not request:
            raise ValueError(f"Invalid request ID: {request_id}")
            
        # Update approval status
        approval = {
            'approver': approver,
            'decision': decision,
            'comments': comments,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        request['approvals'].append(approval)
        
        # Check if all approvals received
        if await self._is_fully_approved(request):
            request['status'] = 'approved'
            await self._execute_approved_query(request)
        elif decision == 'rejected':
            request['status'] = 'rejected'
            
        # Update request
        await self._update_request(request)
        
        # Notify submitter
        await self.notifier.notify_submitter(
            request_id=request['id'],
            submitter=request['submitter'],
            status=request['status']
        )
        
        # Audit logging
        await self.audit.log_approval(request, approval)
        
        return request
        
    async def _determine_approvers(self, analysis: Dict) -> List[str]:
        """Onaylayıcıları belirler."""
        approvers = []
        
        # Risk level'a göre onaylayıcı belirleme
        if analysis['risk_level'] == 'high':
            approvers.extend(await self._get_senior_approvers())
        elif analysis['risk_level'] == 'medium':
            approvers.extend(await self._get_team_leads())
            
        # Impact score'a göre ek onaylayıcılar
        if analysis['impact_score'] > 80:
            approvers.extend(await self._get_db_admins())
            
        return list(set(approvers))  # Remove duplicates