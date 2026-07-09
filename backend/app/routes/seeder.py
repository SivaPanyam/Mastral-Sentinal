from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import require_role
from app.seeder import run_seeder
from pydantic import BaseModel
from typing import List, Any

router = APIRouter(prefix="/seed", tags=["Database Seeder"])

class SeederPayload(BaseModel):
    type: str
    data: List[Any]

@router.post("/")
def trigger_seeder(payload: SeederPayload, db: Session = Depends(get_db), current_user = Depends(require_role(["Admin"]))):
    """Trigger the database seeder framework (Requires Admin role)."""
    try:
        run_seeder(db, payload.type, payload.data)
        return {"status": "success", "message": f"Successfully seeded {payload.type}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
