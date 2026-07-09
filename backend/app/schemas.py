from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# Common types
class ActionItemSchema(BaseModel):
    id: str
    title: str
    status: str  # TODO, DONE
    assignee: str

class TimelineEventSchema(BaseModel):
    timestamp: str
    event: str

# Incident Log schemas
class IncidentLogBase(BaseModel):
    source: str
    level: str
    message: str

class IncidentLogCreate(IncidentLogBase):
    pass

class IncidentLogOut(IncidentLogBase):
    id: str
    incidentId: str
    timestamp: datetime

    class Config:
        from_attributes = True

# Agent Output schemas
class AgentOutputBase(BaseModel):
    agentType: str
    status: str
    summary: str
    payload: Optional[Dict[str, Any]] = None

class AgentOutputCreate(AgentOutputBase):
    pass

class AgentOutputOut(AgentOutputBase):
    id: str
    incidentId: str
    timestamp: datetime

    class Config:
        from_attributes = True

# Report schemas
class ReportBase(BaseModel):
    title: str
    summary: str
    rootCause: str
    impact: str
    timeline: List[TimelineEventSchema]
    actionItems: List[ActionItemSchema]

class ReportCreate(ReportBase):
    incidentId: str
    createdBy: Optional[str] = "Mastra RCA Report Agent"

class ReportOut(ReportBase):
    id: str
    incidentId: str
    createdAt: datetime
    createdBy: str

    class Config:
        from_attributes = True

# Knowledge Source schemas
class KnowledgeSourceBase(BaseModel):
    title: str
    type: str  # RUNBOOK, POST_MORTEM, ARCHITECTURE
    service: str
    content: str

class KnowledgeSourceCreate(KnowledgeSourceBase):
    pass

class KnowledgeSourceOut(KnowledgeSourceBase):
    id: str
    vectorId: Optional[str] = None
    lastUpdated: datetime

    class Config:
        from_attributes = True

# Incident schemas
class IncidentBase(BaseModel):
    title: str
    description: Optional[str] = None
    severity: str
    service: str

class IncidentCreate(IncidentBase):
    pass

class IncidentOut(IncidentBase):
    id: str
    status: str
    createdAt: datetime
    updatedAt: datetime
    acknowledgedAt: Optional[datetime] = None
    resolvedAt: Optional[datetime] = None
    leadTimeSeconds: Optional[int] = None
    logs: List[IncidentLogOut] = []
    agent_outputs: List[AgentOutputOut] = []

    class Config:
        from_attributes = True

# Auth schemas
class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    email: str
    role: str
    refresh_token: Optional[str] = None

class TokenRefreshRequest(BaseModel):
    refresh_token: str

# Analytics schemas
class ServiceHealthOut(BaseModel):
    name: str
    status: str  # HEALTHY, DEGRADED, DOWN
    latencyMs: int
    uptime24h: float

class MetricPointOut(BaseModel):
    date: str
    incidents: int
    mttrMinutes: int

class SystemOverviewOut(BaseModel):
    mttrMinutes: int
    uptimePercentage: float
    activeIncidents: int
    totalIncidents: int
    criticalServicesCount: int
    ragVectorsIndexed: int

# Audit Log schemas
class AuditLogBase(BaseModel):
    action: str
    resourceType: str
    resourceId: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class AuditLogOut(AuditLogBase):
    id: str
    userId: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True

# User schemas
class UserBase(BaseModel):
    name: str
    email: str
    role: str

class UserOut(UserBase):
    id: str
    createdAt: datetime
    updatedAt: datetime
    
    class Config:
        from_attributes = True

# Settings schemas
class SettingsBase(BaseModel):
    theme: str = "dark"
    language: str = "en"
    timezone: str = "UTC"
    default_dashboard: str = "Incident Analytics"
    notifications: Optional[Dict[str, Any]] = None
    ai_preferences: Optional[Dict[str, Any]] = None
    guardrail_settings: Optional[Dict[str, Any]] = None

class SettingsCreate(SettingsBase):
    pass

class SettingsOut(SettingsBase):
    id: str
    userId: str
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

# Copilot schemas
class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    status: str
    message: str
