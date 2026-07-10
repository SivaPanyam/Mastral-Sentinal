from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
import uuid
from app.models import Report
from app.schemas import ReportCreate, ReportOut
from app.crud import ReportRepository

from app.auth import require_role

router = APIRouter(prefix="/reports", tags=["RCA Reports"])

@router.get("/", response_model=List[ReportOut])
def get_reports(db: Session = Depends(get_db)):
    """Retrieve all drafted SRE Post-Mortem RCA Reports."""
    return ReportRepository.get_all(db)


@router.get("/{report_id}", response_model=ReportOut)
def get_report(report_id: str, db: Session = Depends(get_db)):
    """Retrieve a single SRE Post-Mortem RCA Report."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="RCA Report not found")
    return report

@router.patch("/{report_id}", response_model=ReportOut)
def update_report(report_id: str, report_update: ReportCreate, db: Session = Depends(get_db), current_user = Depends(require_role(["Admin", "SRE"]))):
    """Update a report's content."""
    report = ReportRepository.get_by_id(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    for field, value in report_update.model_dump().items():
        setattr(report, field, value)
        
    return ReportRepository.update(db, report)

@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_report(report_id: str, db: Session = Depends(get_db), current_user = Depends(require_role(["Admin"]))):
    """Delete a report."""
    report = ReportRepository.get_by_id(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    ReportRepository.delete(db, report)
    return

@router.get("/incident/{incident_id}", response_model=ReportOut)
def get_report_by_incident(incident_id: str, db: Session = Depends(get_db)):
    """Get report by incident ID."""
    report = ReportRepository.get_by_incident_id(db, incident_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found for this incident")
    return report


@router.post("/", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
def create_report(report_in: ReportCreate, db: Session = Depends(get_db), current_user = Depends(require_role(["Admin", "SRE", "DevOps"]))):
    """Manually document an incident root cause report."""
    from app.auth import EnkryptMiddleware
    
    # SCAN REPORT FOR LEAKS
    scan_summary = EnkryptMiddleware.scan_document(report_in.summary, current_user, db)
    scan_root_cause = EnkryptMiddleware.scan_document(report_in.rootCause, current_user, db)
    
    report_id = f"REP-2026-{uuid.uuid4().hex[:4].upper()}"
    new_report = Report(
        id=report_id,
        incidentId=report_in.incidentId,
        title=report_in.title,
        summary=scan_summary.get("sanitized_text", report_in.summary),
        rootCause=scan_root_cause.get("sanitized_text", report_in.rootCause),
        impact=report_in.impact,
        timeline=[event.dict() if hasattr(event, "dict") else event.model_dump() for event in report_in.timeline],
        actionItems=[item.dict() if hasattr(item, "dict") else item.model_dump() for item in report_in.actionItems],
        createdBy=report_in.createdBy
    )
    return ReportRepository.create(db, new_report)
