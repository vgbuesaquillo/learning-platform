from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.domain.schemas import Activity as ActivitySchema
from app.domain.models import Activity as ActivityModel
from app.infrastructure.database import get_db

router = APIRouter(prefix="/activities", tags=["Activities"])

@router.get("/module/{module_id}", response_model=List[ActivitySchema])
def read_activities_by_module(module_id: UUID, db: Session = Depends(get_db)):
    activities = db.query(ActivityModel).filter(
        ActivityModel.module_id == module_id
    ).order_by(ActivityModel.order_index).all()
    return activities
