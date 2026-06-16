from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid
import asyncio

from models import get_db, Project, AnalysisVersion, Room, BOQItem, Organization
from models.analytics import (
    AnalyticsSnapshot, CostTrend, CostBreakdown, MaterialStatistic,
    MaterialCostBreakdown, AIQualityMetric, RoomTypeCorrectionStat
)
from auth.clerk import get_current_user
from services.storage import storage_service
from blueprint_logic import analyze_blueprint

router = APIRouter(prefix="/analysis", tags=["analysis"])

class AnalysisCreate(BaseModel):
    project_id: str
    blueprint_file_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None

class AnalysisResponse(BaseModel):
    id: str
    project_id: str
    version_number: int
    name: Optional[str]
    status: str
    total_area_sqft: Optional[float]
    room_count: Optional[int]
    created_at: datetime

async def run_analysis_task(
    analysis_id: str,
    file_bytes: bytes,
    filename: str
):
    """Background task to run blueprint analysis"""
    from models import engine, SessionLocal
    
    db = SessionLocal()
    try:
        # Get analysis record
        analysis = db.query(AnalysisVersion).filter(AnalysisVersion.id == uuid.UUID(analysis_id)).first()
        if not analysis:
            return
        
        # Run the existing blueprint analysis
        result = analyze_blueprint(file_bytes, filename)
        
        # Update analysis with results
        analysis.status = 'completed'
        analysis.completed_at = datetime.utcnow()
        analysis.total_area_sqft = result.get('total_area')
        room_data = result.get('room_data', [])
        analysis.room_count = len(room_data)
        analysis.floor_count = result.get('floor_count')
        analysis.door_count = result.get('door_count')
        analysis.window_count = result.get('window_count')
        quality = result.get('extraction_quality', {})
        analysis.confidence_score = quality.get('score', quality.get('avg_confidence', 0))
        analysis.raw_result = result
        
        db.commit()
        
        # Create room records
        rooms = room_data
        for room_data in rooms:
            room = Room(
                analysis_version_id=analysis.id,
                name=room_data.get('room', room_data.get('label', 'Unknown')),
                room_type=room_data.get('room'),
                area_sqft=room_data.get('area'),
                width_ft=room_data.get('width'),
                height_ft=room_data.get('height'),
                confidence_score=room_data.get('confidence'),
                source='ai_analysis',
                polygon_coordinates=room_data.get('polygon')
            )
            db.add(room)
        
        # Create BOQ items
        boq_items = result.get('boq_items', [])
        for item_data in boq_items:
            item = BOQItem(
                analysis_version_id=analysis.id,
                category=item_data.get('category'),
                description=item_data.get('description'),
                unit=item_data.get('unit'),
                quantity=item_data.get('quantity'),
                rate=item_data.get('rate'),
                amount=item_data.get('amount'),
                source='calculated'
            )
            db.add(item)
        
        db.commit()
        
        # Populate analytics tables
        project = db.query(Project).filter(Project.id == analysis.project_id).first()
        if project:
            organization = db.query(Organization).filter(Organization.id == project.organization_id).first()
            if organization:
                # Create analytics snapshot
                snapshot = AnalyticsSnapshot(
                    organization_id=organization.id,
                    project_id=project.id,
                    analysis_version_id=analysis.id,
                    snapshot_date=datetime.utcnow(),
                    total_projects=1,
                    active_projects=1 if project.status == 'active' else 0,
                    completed_projects=1 if project.status == 'completed' else 0,
                    total_floor_area_sqft=analysis.total_area_sqft or 0,
                    total_boq_value=sum([item.amount for item in boq_items]) if boq_items else 0,
                    avg_cost_per_sqft=(sum([item.amount for item in boq_items]) / analysis.total_area_sqft) if analysis.total_area_sqft and boq_items else 0,
                    avg_project_cost=sum([item.amount for item in boq_items]) if boq_items else 0,
                    total_material_quantity=sum([item.quantity for item in boq_items if item.unit in ['tons', 'kg', 'units']]) if boq_items else 0,
                    total_analyses=1,
                    total_corrections=0,
                    total_approvals=0,
                    total_exports=0
                )
                db.add(snapshot)
                
                # Create cost trend entry
                cost_trend = CostTrend(
                    organization_id=organization.id,
                    project_id=project.id,
                    snapshot_date=datetime.utcnow(),
                    total_cost=sum([item.amount for item in boq_items]) if boq_items else 0,
                    material_cost=sum([item.amount for item in boq_items if item.category in ['Civil', 'Flooring']]) if boq_items else 0,
                    labour_cost=sum([item.amount for item in boq_items if item.category in ['Labour']]) if boq_items else 0,
                    overhead_cost=sum([item.amount for item in boq_items if item.category in ['Overhead']]) if boq_items else 0,
                    cost_per_sqft=(sum([item.amount for item in boq_items]) / analysis.total_area_sqft) if analysis.total_area_sqft and boq_items else 0
                )
                db.add(cost_trend)
                
                # Create cost breakdown entries
                if boq_items:
                    category_totals = {}
                    for item in boq_items:
                        category = item.category or 'Other'
                        if category not in category_totals:
                            category_totals[category] = 0
                        category_totals[category] += item.amount
                    
                    total_cost = sum(category_totals.values())
                    for category, cost in category_totals.items():
                        breakdown = CostBreakdown(
                            organization_id=organization.id,
                            project_id=project.id,
                            category=category,
                            cost=cost,
                            percentage=(cost / total_cost * 100) if total_cost > 0 else 0,
                            snapshot_date=datetime.utcnow()
                        )
                        db.add(breakdown)
                
                # Create material statistics
                if boq_items:
                    material_totals = {}
                    for item in boq_items:
                        material = item.description or 'Unknown'
                        if material not in material_totals:
                            material_totals[material] = {'quantity': 0, 'cost': 0, 'unit': item.unit}
                        material_totals[material]['quantity'] += item.quantity or 0
                        material_totals[material]['cost'] += item.amount or 0
                    
                    for material, data in material_totals.items():
                        material_stat = MaterialStatistic(
                            organization_id=organization.id,
                            project_id=project.id,
                            material_name=material,
                            total_quantity=data['quantity'],
                            unit=data['unit'],
                            total_cost=data['cost'],
                            snapshot_date=datetime.utcnow()
                        )
                        db.add(material_stat)
                
                # Create AI quality metrics
                ai_quality = AIQualityMetric(
                    organization_id=organization.id,
                    project_id=project.id,
                    analysis_version_id=analysis.id,
                    snapshot_date=datetime.utcnow(),
                    total_rooms_detected=len(rooms),
                    high_confidence_rooms=len([r for r in rooms if (r.confidence_score or 0) > 0.8]),
                    medium_confidence_rooms=len([r for r in rooms if 0.5 <= (r.confidence_score or 0) <= 0.8]),
                    low_confidence_rooms=len([r for r in rooms if (r.confidence_score or 0) < 0.5]),
                    rooms_corrected=0,
                    manual_corrections=0,
                    accuracy_rate=(len([r for r in rooms if (r.confidence_score or 0) > 0.8]) / len(rooms) * 100) if rooms else 0,
                    avg_confidence_score=sum([r.confidence_score or 0 for r in rooms]) / len(rooms) if rooms else 0
                )
                db.add(ai_quality)
                
                # Create room type correction stats
                if rooms:
                    room_type_counts = {}
                    for room in rooms:
                        room_type = room.room_type or 'Unknown'
                        if room_type not in room_type_counts:
                            room_type_counts[room_type] = {'total': 0, 'corrections': 0}
                        room_type_counts[room_type]['total'] += 1
                    
                    for room_type, data in room_type_counts.items():
                        room_type_stat = RoomTypeCorrectionStat(
                            organization_id=organization.id,
                            project_id=project.id,
                            room_type=room_type,
                            total_detections=data['total'],
                            total_corrections=data['corrections'],
                            correction_rate=(data['corrections'] / data['total'] * 100) if data['total'] > 0 else 0,
                            snapshot_date=datetime.utcnow()
                        )
                        db.add(room_type_stat)
                
                db.commit()
        
    except Exception as e:
        print(f"Analysis failed: {e}")
        analysis.status = 'failed'
        db.commit()
    finally:
        db.close()

@router.post("/start", response_model=AnalysisResponse)
async def start_analysis(
    analysis: AnalysisCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a new blueprint analysis"""
    
    # Verify project exists
    project = db.query(Project).filter(Project.id == uuid.UUID(analysis.project_id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get next version number
    last_version = db.query(AnalysisVersion).filter(
        AnalysisVersion.project_id == uuid.UUID(analysis.project_id)
    ).order_by(AnalysisVersion.version_number.desc()).first()
    
    version_number = (last_version.version_number + 1) if last_version else 1
    
    # Create analysis version
    new_analysis = AnalysisVersion(
        project_id=uuid.UUID(analysis.project_id),
        blueprint_file_id=uuid.UUID(analysis.blueprint_file_id) if analysis.blueprint_file_id else None,
        version_number=version_number,
        name=analysis.name or f"Version {version_number}",
        description=analysis.description,
        status='processing',
        created_by=uuid.UUID(current_user.get('sub')) if current_user.get('sub') else None
    )
    
    db.add(new_analysis)
    db.commit()
    db.refresh(new_analysis)
    
    # For now, we'll need the file to be provided separately
    # This would be integrated with the file upload system
    
    return AnalysisResponse(
        id=str(new_analysis.id),
        project_id=str(new_analysis.project_id),
        version_number=new_analysis.version_number,
        name=new_analysis.name,
        status=new_analysis.status,
        total_area_sqft=float(new_analysis.total_area_sqft) if new_analysis.total_area_sqft else None,
        room_count=new_analysis.room_count,
        created_at=new_analysis.created_at
    )

@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(
    analysis_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get analysis by ID"""
    
    analysis = db.query(AnalysisVersion).filter(AnalysisVersion.id == uuid.UUID(analysis_id)).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Check user has access to the project
    clerk_user_id = current_user.get('sub')
    if clerk_user_id:
        from models import User, OrganizationMember
        user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
        if user:
            # Get project and check organization access
            project = db.query(Project).filter(Project.id == analysis.project_id).first()
            if project:
                user_org_ids = [m.organization_id for m in db.query(OrganizationMember).filter(OrganizationMember.user_id == user.id).all()]
                if project.organization_id not in user_org_ids:
                    raise HTTPException(status_code=403, detail="Access denied to this analysis")
    
    return AnalysisResponse(
        id=str(analysis.id),
        project_id=str(analysis.project_id),
        version_number=analysis.version_number,
        name=analysis.name,
        status=analysis.status,
        total_area_sqft=float(analysis.total_area_sqft) if analysis.total_area_sqft else None,
        room_count=analysis.room_count,
        created_at=analysis.created_at
    )

@router.get("/project/{project_id}", response_model=list[AnalysisResponse])
async def list_project_analyses(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all analyses for a project"""
    
    # Check user has access to the project
    clerk_user_id = current_user.get('sub')
    if clerk_user_id:
        from models import User, OrganizationMember
        user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
        if user:
            project = db.query(Project).filter(Project.id == uuid.UUID(project_id)).first()
            if project:
                user_org_ids = [m.organization_id for m in db.query(OrganizationMember).filter(OrganizationMember.user_id == user.id).all()]
                if project.organization_id not in user_org_ids:
                    raise HTTPException(status_code=403, detail="Access denied to this project")
    
    analyses = db.query(AnalysisVersion).filter(
        AnalysisVersion.project_id == uuid.UUID(project_id)
    ).order_by(AnalysisVersion.version_number.desc()).all()
    
    return [
        AnalysisResponse(
            id=str(a.id),
            project_id=str(a.project_id),
            version_number=a.version_number,
            name=a.name,
            status=a.status,
            total_area_sqft=float(a.total_area_sqft) if a.total_area_sqft else None,
            room_count=a.room_count,
            created_at=a.created_at
        )
        for a in analyses
    ]
