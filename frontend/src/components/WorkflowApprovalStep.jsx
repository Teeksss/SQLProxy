import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { CheckCircle, XCircle, Clock, AlertCircle, User, UserCircle, Users, ShieldCheck } from 'lucide-react';

/**
 * Component that displays a step in an approval workflow
 * 
 * @param {Object} props Component props
 * @param {Object} props.step Step information
 * @param {boolean} props.isCurrent Whether this is the current step
 * @param {Function} props.onApprove Function to call when step is approved
 * @param {Function} props.onReject Function to call when step is rejected
 * @param {string} props.currentUser Current username
 * @param {string} props.userRole Current user role
 * @returns {JSX.Element} Workflow approval step component
 */
const WorkflowApprovalStep = ({ 
  step, 
  isCurrent = false, 
  onApprove, 
  onReject,
  currentUser,
  userRole
}) => {
  const [comment, setComment] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  if (!step) return null;
  
  // Check if current user can approve this step
  const canApprove = () => {
    if (step.status !== 'pending') return false;
    if (!isCurrent) return false;
    
    // Check approver type
    if (step.approver_type === 'user') {
      const approvers = step.approver_value.split(',').map(a => a.trim());
      return approvers.includes(currentUser);
    } else if (step.approver_type === 'role') {
      const roles = step.approver_value.split(',').map(r => r.trim());
      return roles.includes(userRole);
    }
    
    return false;
  };
  
  // Get status icon and color
  const getStatusInfo = () => {
    switch (step.status) {
      case 'approved':
        return { 
          icon: <CheckCircle className="h-5 w-5" />, 
          color: 'bg-green-100 text-green-700 border-green-200',
          text: 'Onaylandı'
        };
      case 'rejected':
        return { 
          icon: <XCircle className="h-5 w-5" />, 
          color: 'bg-red-100 text-red-700 border-red-200',
          text: 'Reddedildi'
        };
      case 'skipped':
        return { 
          icon: <AlertCircle className="h-5 w-5" />, 
          color: 'bg-yellow-100 text-yellow-700 border-yellow-200',
          text: 'Atlandı'
        };
      default:
        return { 
          icon: <Clock className="h-5 w-5" />, 
          color: 'bg-blue-100 text-blue-700 border-blue-200',
          text: 'Bekliyor'
        };
    }
  };
  
  // Get approver icon based on type
  const getApproverIcon = () => {
    switch (step.approver_type) {
      case 'user':
        return <User className="h-4 w-4 mr-1" />;
      case 'role':
        return <ShieldCheck className="h-4 w-4 mr-1" />;
      case 'group':
        return <Users className="h-4 w-4 mr-1" />;
      default:
        return <UserCircle className="h-4 w-4 mr-1" />;
    }
  };
  
  // Handle approve click
  const handleApprove = async () => {
    if (!canApprove()) return;
    
    setIsSubmitting(true);
    try {
      await onApprove(step.id, comment);
    } finally {
      setIsSubmitting(false);
    }
  };
  
  // Handle reject click
  const handleReject = async () => {
    if (!canApprove()) return;
    if (!comment.trim()) {
      // Require a comment for rejection
      alert('Reddetme işlemi için açıklama gereklidir.');
      return;
    }
    
    setIsSubmitting(true);
    try {
      await onReject(step.id, comment);
    } finally {
      setIsSubmitting(false);
    }
  };
  
  const statusInfo = getStatusInfo();
  const isUserApprover = canApprove();
  
  // Determine if step is current, completed, or upcoming
  let stepState = "upcoming";
  if (isCurrent) {
    stepState = "current";
  } else if (step.status !== 'pending') {
    stepState = "completed";
  }
  
  return (
    <Card className={`mb-4 ${isCurrent ? 'border-blue-400 shadow-md' : step.status !== 'pending' ? 'opacity-80' : 'opacity-70'}`}>
      <CardHeader className={`pb-3 ${isCurrent ? 'bg-blue-50' : step.status !== 'pending' ? 'bg-gray-50' : ''}`}>
        <div className="flex justify-between items-start">
          <div>
            <CardTitle className="text-base flex items-center">
              {step.step_order}. {step.name}
              {!step.is_required && (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Badge variant="outline" className="ml-2 text-xs">Opsiyonel</Badge>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Bu adım opsiyoneldir, onay sürecini durdurmaz</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
            </CardTitle>
            <CardDescription className="text-sm mt-1">
              {step.description || 'Bu onay adımının açıklaması bulunmamaktadır.'}
            </CardDescription>
          </div>
          
          <Badge className={`${statusInfo.color} flex items-center gap-1`}>
            {statusInfo.icon}
            <span>{statusInfo.text}</span>
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent className="pt-3">
        <div className="flex items-center text-sm text-gray-600 mb-3">
          <div className="flex items-center">
            {getApproverIcon()}
            <span className="font-medium mr-1">Onaylayıcı:</span>
          </div>
          <span>
            {step.approver_type === 'user' 
              ? step.approver_value 
              : `${step.approver_type === 'role' ? 'Rol' : 'Grup'}: ${step.approver_value}`}
          </span>
        </div>
        
        {step.status !== 'pending' && (
          <div className="mt-3 border-t pt-3">
            <div className="flex items-center gap-2 mb-2">
              <Avatar className="h-6 w-6">
                <AvatarFallback>{step.approved_by?.[0] || '?'}</AvatarFallback>
              </Avatar>
              <div className="text-sm font-medium">{step.approved_by || 'Sistem'}</div>
              <div className="text-xs text-gray-500">
                {step.approved_at ? new Date(step.approved_at).toLocaleString() : ''}
              </div>
            </div>
            
            {step.approver_comment && (
              <div className="bg-gray-50 p-3 rounded-md text-sm text-gray-700 mt-1">
                {step.approver_comment}
              </div>
            )}
          </div>
        )}
        
        {isCurrent && isUserApprover && (
          <div className="mt-4">
            <Textarea
              placeholder="Onay veya red için açıklama (opsiyonel, red için zorunlu)"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              className="mb-3"
            />
          </div>
        )}
      </CardContent>
      
      {isCurrent && isUserApprover && (
        <CardFooter className="flex justify-end space-x-2 pt-2 border-t">
          <Button 
            variant="outline" 
            onClick={handleReject}
            disabled={isSubmitting}
            className="bg-red-50 border-red-200 text-red-700 hover:bg-red-100 hover:text-red-800"
          >
            <XCircle className="h-4 w-4 mr-1" />
            Reddet
          </Button>
          
          <Button 
            variant="default" 
            onClick={handleApprove}
            disabled={isSubmitting}
          >
            <CheckCircle className="h-4 w-4 mr-1" />
            Onayla
          </Button>
        </CardFooter>
      )}
    </Card>
  );
};

// Son güncelleme: 2025-05-20 10:00:16
// Güncelleyen: Teeksss

export default WorkflowApprovalStep;