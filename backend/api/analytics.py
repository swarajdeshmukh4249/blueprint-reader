from fastapi import APIRouter, Depends, HTTPException, Query, Header
from fastapi.responses import Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date, timedelta
import uuid
import csv
import io

from models import get_db, AnalyticsSnapshot, CostTrend, CostBreakdown, MaterialStatistic, MaterialCostBreakdown
from models import RegionalCostRate, RegionalCostHistory, AIQualityMetric, RoomTypeCorrectionStat
from models import RevisionAnalytic, TeamActivityMetric, PortfolioAnalytic, ApprovalAnalytic, BenchmarkingData
from models import Project, AnalysisVersion, Room, BOQItem, Organization, User
from auth.clerk import get_current_user_db
from services.activity_service import ActivityService
from utils.org_filtering import verify_user_org_access

router = APIRouter(prefix="/analytics", tags=["analytics"])


# SECTION 1: Executive KPI Dashboard
class ExecutiveKPIs(BaseModel):
    total_projects: int
    active_projects: int
    completed_projects: int
    total_floor_area_sqft: float
    total_boq_value: float
    avg_cost_per_sqft: float
    avg_project_cost: float
    projects_trend: float
    boq_value_trend: float
    cost_per_sqft_trend: float


@router.get("/executive-kpis/{organization_id}", response_model=ExecutiveKPIs)
async def get_executive_kpis(
    organization_id: str,
    period: str = Query("monthly", pattern="^(daily|weekly|monthly|yearly)$"),
    current_user: User = Depends(get_current_user_db),
    db: Session = Depends(get_db)
):
    """Get executive KPIs for organization. Requires user to be a member of the organization."""
    
    try:
        org_uuid = uuid.UUID(organization_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid organization_id format")
    
    # Verify user has access to this organization
    if not verify_user_org_access(current_user.id, org_uuid, db):
        raise HTTPException(status_code=403, detail="User does not have access to this organization")
    
    # Get latest snapshot
    snapshot = db.query(AnalyticsSnapshot).filter(
        AnalyticsSnapshot.organization_id == org_uuid,
        AnalyticsSnapshot.period_type == period
    ).order_by(AnalyticsSnapshot.snapshot_date.desc()).first()
    
    if not snapshot:
        # Calculate from live data if no snapshot exists
        projects = db.query(Project).filter(
            Project.organization_id == uuid.UUID(organization_id)
        ).all()
        
        total_projects = len(projects)
        active_projects = len([p for p in projects if p.status == 'active'])
        completed_projects = len([p for p in projects if p.status == 'completed'])
        
        # Get total area and BOQ from analysis versions
        analyses = db.query(AnalysisVersion).join(Project).filter(
            Project.organization_id == uuid.UUID(organization_id)
        ).all()
        
        total_floor_area_sqft = sum(float(a.total_area_sqft or 0) for a in analyses)
        total_boq_value = sum(float(a.raw_result.get('total_cost', 0)) if a.raw_result else 0 for a in analyses)
        
        avg_cost_per_sqft = total_boq_value / total_floor_area_sqft if total_floor_area_sqft > 0 else 0
        avg_project_cost = total_boq_value / total_projects if total_projects > 0 else 0
        
        return ExecutiveKPIs(
            total_projects=total_projects,
            active_projects=active_projects,
            completed_projects=completed_projects,
            total_floor_area_sqft=total_floor_area_sqft,
            total_boq_value=total_boq_value,
            avg_cost_per_sqft=avg_cost_per_sqft,
            avg_project_cost=avg_project_cost,
            projects_trend=0,
            boq_value_trend=0,
            cost_per_sqft_trend=0
        )
    
    return ExecutiveKPIs(
        total_projects=snapshot.total_projects,
        active_projects=snapshot.active_projects,
        completed_projects=snapshot.completed_projects,
        total_floor_area_sqft=float(snapshot.total_floor_area_sqft or 0),
        total_boq_value=float(snapshot.total_boq_value or 0),
        avg_cost_per_sqft=float(snapshot.avg_cost_per_sqft or 0),
        avg_project_cost=float(snapshot.avg_project_cost or 0),
        projects_trend=float(snapshot.projects_trend or 0),
        boq_value_trend=float(snapshot.boq_value_trend or 0),
        cost_per_sqft_trend=float(snapshot.cost_per_sqft_trend or 0)
    )


# SECTION 2: Cost Analytics
class CostTrendData(BaseModel):
    date: str
    total_cost: float
    material_cost: float
    labour_cost: float
    overhead_cost: float


@router.get("/cost-trends/{organization_id}", response_model=List[CostTrendData])
async def get_cost_trends(
    organization_id: str,
    project_id: Optional[str] = None,
    start_date: date = Query(...),
    end_date: date = Query(...),
    current_user: User = Depends(get_current_user_db),
    db: Session = Depends(get_db)
):
    """Get cost trends over time"""
    
    try:
        org_uuid = uuid.UUID(organization_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid organization_id format")
    
    if not verify_user_org_access(current_user.id, org_uuid, db):
        raise HTTPException(status_code=403, detail="User does not have access to this organization")
    
    query = db.query(CostTrend).filter(
        CostTrend.organization_id == org_uuid,
        CostTrend.record_date >= start_date,
        CostTrend.record_date <= end_date
    )
    
    if project_id:
        query = query.filter(CostTrend.project_id == uuid.UUID(project_id))
    
    trends = query.order_by(CostTrend.record_date).all()
    
    return [
        CostTrendData(
            date=t.record_date.isoformat(),
            total_cost=float(t.total_cost or 0),
            material_cost=float(t.material_cost or 0),
            labour_cost=float(t.labour_cost or 0),
            overhead_cost=float(t.overhead_cost or 0)
        )
        for t in trends
    ]


class CostBreakdownItem(BaseModel):
    category: str
    cost: float
    percentage: float


@router.get("/cost-breakdown/{organization_id}", response_model=List[CostBreakdownItem])
async def get_cost_breakdown(
    organization_id: str,
    project_id: Optional[str] = None,
    current_user: User = Depends(get_current_user_db),
    db: Session = Depends(get_db)
):
    """Get cost breakdown by category"""
    
    try:
        org_uuid = uuid.UUID(organization_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid organization_id format")
    
    if not verify_user_org_access(current_user.id, org_uuid, db):
        raise HTTPException(status_code=403, detail="User does not have access to this organization")
    
    query = db.query(CostBreakdown).filter(
        CostBreakdown.organization_id == org_uuid
    )
    
    if project_id:
        query = query.filter(CostBreakdown.project_id == uuid.UUID(project_id))
    
    breakdowns = query.all()
    
    return [
        CostBreakdownItem(
            category=b.category,
            cost=float(b.cost or 0),
            percentage=float(b.percentage or 0)
        )
        for b in breakdowns
    ]


class CostPerSqFtItem(BaseModel):
    project_id: str
    project_name: str
    area_sqft: float
    total_cost: float
    cost_per_sqft: float


@router.get("/cost-per-sqft/{organization_id}", response_model=List[CostPerSqFtItem])
async def get_cost_per_sqft(
    organization_id: str,
    db: Session = Depends(get_db)
):
    """Get cost per sq ft for all projects"""
    
    projects = db.query(Project).filter(
        Project.organization_id == uuid.UUID(organization_id)
    ).all()
    
    result = []
    for project in projects:
        # Get latest analysis
        analysis = db.query(AnalysisVersion).filter(
            AnalysisVersion.project_id == project.id
        ).order_by(AnalysisVersion.version_number.desc()).first()
        
        if analysis and analysis.total_area_sqft and analysis.raw_result:
            total_cost = analysis.raw_result.get('total_cost', 0)
            area = float(analysis.total_area_sqft)
            cost_per_sqft = total_cost / area if area > 0 else 0
            
            result.append(CostPerSqFtItem(
                project_id=str(project.id),
                project_name=project.name,
                area_sqft=area,
                total_cost=total_cost,
                cost_per_sqft=cost_per_sqft
            ))
    
    return result


# SECTION 3: Material Analytics
class MaterialQuantity(BaseModel):
    material_name: str
    quantity: float
    unit: str
    cost: float


@router.get("/material-quantities/{organization_id}", response_model=List[MaterialQuantity])
async def get_material_quantities(
    organization_id: str,
    project_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get material quantities"""
    
    query = db.query(MaterialStatistic).filter(
        MaterialStatistic.organization_id == uuid.UUID(organization_id)
    )
    
    if project_id:
        query = query.filter(MaterialStatistic.project_id == uuid.UUID(project_id))
    
    materials = query.all()
    
    return [
        MaterialQuantity(
            material_name=m.material_name,
            quantity=float(m.quantity or 0),
            unit=m.unit,
            cost=float(m.cost or 0)
        )
        for m in materials
    ]


class MaterialCostItem(BaseModel):
    material_name: str
    cost: float
    quantity: float
    cost_per_unit: float


@router.get("/material-cost-breakdown/{organization_id}", response_model=List[MaterialCostItem])
async def get_material_cost_breakdown(
    organization_id: str,
    project_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get material cost breakdown"""
    
    query = db.query(MaterialCostBreakdown).filter(
        MaterialCostBreakdown.organization_id == uuid.UUID(organization_id)
    )
    
    if project_id:
        query = query.filter(MaterialCostBreakdown.project_id == uuid.UUID(project_id))
    
    breakdowns = query.all()
    
    return [
        MaterialCostItem(
            material_name=b.material_name,
            cost=float(b.cost or 0),
            quantity=float(b.quantity or 0),
            cost_per_unit=float(b.cost_per_unit or 0)
        )
        for b in breakdowns
    ]


# SECTION 4: Regional Cost Intelligence
class RegionalRate(BaseModel):
    id: str
    country: str
    state: Optional[str]
    city: str
    material_name: str
    current_rate: float
    unit: str
    trend: str
    trend_percentage: float


@router.get("/regional-rates/{organization_id}", response_model=List[RegionalRate])
async def get_regional_rates(
    organization_id: str,
    city: Optional[str] = None,
    material_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get regional cost rates"""
    
    query = db.query(RegionalCostRate).filter(
        RegionalCostRate.organization_id == uuid.UUID(organization_id)
    )
    
    if city:
        query = query.filter(RegionalCostRate.city == city)
    
    if material_name:
        query = query.filter(RegionalCostRate.material_name == material_name)
    
    rates = query.all()
    
    return [
        RegionalRate(
            id=str(r.id),
            country=r.country,
            state=r.state,
            city=r.city,
            material_name=r.material_name,
            current_rate=float(r.current_rate),
            unit=r.unit,
            trend=r.trend,
            trend_percentage=float(r.trend_percentage or 0)
        )
        for r in rates
    ]


class RegionalCostHistoryItem(BaseModel):
    date: str
    rate: float


@router.get("/regional-history/{rate_id}", response_model=List[RegionalCostHistoryItem])
async def get_regional_history(
    rate_id: str,
    days: int = Query(90, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get regional cost history"""
    
    start_date = date.today() - timedelta(days=days)
    
    history = db.query(RegionalCostHistory).filter(
        RegionalCostHistory.regional_rate_id == uuid.UUID(rate_id),
        RegionalCostHistory.record_date >= start_date
    ).order_by(RegionalCostHistory.record_date).all()
    
    return [
        RegionalCostHistoryItem(
            date=h.record_date.isoformat(),
            rate=float(h.rate)
        )
        for h in history
    ]


# SECTION 5: AI Analysis Quality Dashboard
class AIQualityMetrics(BaseModel):
    total_rooms_detected: int
    high_confidence_rooms: int
    medium_confidence_rooms: int
    low_confidence_rooms: int
    rooms_corrected: int
    manual_corrections: int
    accuracy_rate: float
    avg_confidence_score: float


@router.get("/ai-quality/{organization_id}", response_model=AIQualityMetrics)
async def get_ai_quality_metrics(
    organization_id: str,
    project_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get AI quality metrics"""
    
    query = db.query(AIQualityMetric).filter(
        AIQualityMetric.organization_id == uuid.UUID(organization_id)
    )
    
    if project_id:
        query = query.filter(AIQualityMetric.project_id == uuid.UUID(project_id))
    
    metrics = query.all()
    
    # Aggregate metrics
    total_rooms = sum(m.total_rooms_detected or 0 for m in metrics)
    high_conf = sum(m.high_confidence_rooms or 0 for m in metrics)
    medium_conf = sum(m.medium_confidence_rooms or 0 for m in metrics)
    low_conf = sum(m.low_confidence_rooms or 0 for m in metrics)
    corrected = sum(m.rooms_corrected or 0 for m in metrics)
    manual_corr = sum(m.manual_corrections or 0 for m in metrics)
    
    accuracy_rate = (corrected / total_rooms * 100) if total_rooms > 0 else 0
    avg_confidence = sum(m.avg_confidence_score or 0 for m in metrics) / len(metrics) if metrics else 0
    
    return AIQualityMetrics(
        total_rooms_detected=total_rooms,
        high_confidence_rooms=high_conf,
        medium_confidence_rooms=medium_conf,
        low_confidence_rooms=low_conf,
        rooms_corrected=corrected,
        manual_corrections=manual_corr,
        accuracy_rate=accuracy_rate,
        avg_confidence_score=avg_confidence
    )


class RoomTypeCorrection(BaseModel):
    room_type: str
    total_detections: int
    total_corrections: int
    correction_rate: float


@router.get("/room-type-corrections/{organization_id}", response_model=List[RoomTypeCorrection])
async def get_room_type_corrections(
    organization_id: str,
    db: Session = Depends(get_db)
):
    """Get room type correction statistics"""
    
    stats = db.query(RoomTypeCorrectionStat).filter(
        RoomTypeCorrectionStat.organization_id == uuid.UUID(organization_id)
    ).order_by(RoomTypeCorrectionStat.correction_rate.desc()).all()
    
    return [
        RoomTypeCorrection(
            room_type=s.room_type,
            total_detections=s.total_detections,
            total_corrections=s.total_corrections,
            correction_rate=float(s.correction_rate or 0)
        )
        for s in stats
    ]


# SECTION 6: Revision Analytics
class RevisionData(BaseModel):
    from_version_id: str
    to_version_id: str
    area_change_sqft: float
    boq_change: float
    cost_change: float
    rooms_added: int
    rooms_deleted: int
    rooms_modified: int
    created_at: datetime


@router.get("/revisions/{project_id}", response_model=List[RevisionData])
async def get_revision_analytics(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Get revision analytics for a project"""
    
    revisions = db.query(RevisionAnalytic).filter(
        RevisionAnalytic.project_id == uuid.UUID(project_id)
    ).order_by(RevisionAnalytic.created_at).all()
    
    return [
        RevisionData(
            from_version_id=str(r.from_version_id) if r.from_version_id else "",
            to_version_id=str(r.to_version_id) if r.to_version_id else "",
            area_change_sqft=float(r.area_change_sqft or 0),
            boq_change=float(r.boq_change or 0),
            cost_change=float(r.cost_change or 0),
            rooms_added=r.rooms_added or 0,
            rooms_deleted=r.rooms_deleted or 0,
            rooms_modified=r.rooms_modified or 0,
            created_at=r.created_at
        )
        for r in revisions
    ]


# SECTION 7: Portfolio Analytics
class PortfolioMetrics(BaseModel):
    total_portfolio_value: float
    total_area_sqft: float
    total_buildings: int
    total_floors: int
    residential_count: int
    commercial_count: int
    industrial_count: int
    mixed_use_count: int


@router.get("/portfolio/{organization_id}", response_model=PortfolioMetrics)
async def get_portfolio_analytics(
    organization_id: str,
    db: Session = Depends(get_db)
):
    """Get portfolio analytics"""
    
    portfolio = db.query(PortfolioAnalytic).filter(
        PortfolioAnalytic.organization_id == uuid.UUID(organization_id)
    ).order_by(PortfolioAnalytic.snapshot_date.desc()).first()
    
    if not portfolio:
        # Calculate from live data
        projects = db.query(Project).filter(
            Project.organization_id == uuid.UUID(organization_id)
        ).all()
        
        analyses = db.query(AnalysisVersion).join(Project).filter(
            Project.organization_id == uuid.UUID(organization_id)
        ).all()
        
        total_area = sum(float(a.total_area_sqft or 0) for a in analyses)
        total_value = sum(float(a.raw_result.get('total_cost', 0)) if a.raw_result else 0 for a in analyses)
        
        return PortfolioMetrics(
            total_portfolio_value=total_value,
            total_area_sqft=total_area,
            total_buildings=len(projects),
            total_floors=0,  # Would need to be calculated from analysis data
            residential_count=0,
            commercial_count=0,
            industrial_count=0,
            mixed_use_count=0
        )
    
    return PortfolioMetrics(
        total_portfolio_value=float(portfolio.total_portfolio_value or 0),
        total_area_sqft=float(portfolio.total_area_sqft or 0),
        total_buildings=portfolio.total_buildings or 0,
        total_floors=portfolio.total_floors or 0,
        residential_count=portfolio.residential_count or 0,
        commercial_count=portfolio.commercial_count or 0,
        industrial_count=portfolio.industrial_count or 0,
        mixed_use_count=portfolio.mixed_use_count or 0
    )


# SECTION 8: Team Analytics
class TeamActivityItem(BaseModel):
    user_id: str
    activity_date: str
    analyses_run: int
    reports_exported: int
    comments_added: int
    corrections_made: int
    approvals_given: int


@router.get("/team-activity/{organization_id}", response_model=List[TeamActivityItem])
async def get_team_activity(
    organization_id: str,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db)
):
    """Get team activity metrics"""
    
    activities = db.query(TeamActivityMetric).filter(
        TeamActivityMetric.organization_id == uuid.UUID(organization_id),
        TeamActivityMetric.activity_date >= start_date,
        TeamActivityMetric.activity_date <= end_date
    ).order_by(TeamActivityMetric.activity_date).all()
    
    return [
        TeamActivityItem(
            user_id=str(a.user_id) if a.user_id else "",
            activity_date=a.activity_date.isoformat(),
            analyses_run=a.analyses_run or 0,
            reports_exported=a.reports_exported or 0,
            comments_added=a.comments_added or 0,
            corrections_made=a.corrections_made or 0,
            approvals_given=a.approvals_given or 0
        )
        for a in activities
    ]


# SECTION 9: Approval Workflow Analytics
class ApprovalMetrics(BaseModel):
    pending_approvals: int
    approved_reports: int
    rejected_reports: int
    avg_approval_time_hours: float


@router.get("/approval-metrics/{organization_id}", response_model=ApprovalMetrics)
async def get_approval_metrics(
    organization_id: str,
    db: Session = Depends(get_db)
):
    """Get approval workflow metrics"""
    
    approval_analytics = db.query(ApprovalAnalytic).filter(
        ApprovalAnalytic.organization_id == uuid.UUID(organization_id)
    ).order_by(ApprovalAnalytic.snapshot_date.desc()).first()
    
    if not approval_analytics:
        return ApprovalMetrics(
            pending_approvals=0,
            approved_reports=0,
            rejected_reports=0,
            avg_approval_time_hours=0
        )
    
    return ApprovalMetrics(
        pending_approvals=approval_analytics.pending_approvals or 0,
        approved_reports=approval_analytics.approved_reports or 0,
        rejected_reports=approval_analytics.rejected_reports or 0,
        avg_approval_time_hours=float(approval_analytics.avg_approval_time_hours or 0)
    )


# SECTION 10: Audit & Compliance Analytics
@router.get("/audit-summary/{organization_id}")
async def get_audit_summary(
    organization_id: str,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db)
):
    """Get audit summary for compliance"""
    
    # This would query the audit_logs table
    from models import AuditLog
    
    logs = db.query(AuditLog).filter(
        AuditLog.organization_id == uuid.UUID(organization_id),
        AuditLog.created_at >= start_date,
        AuditLog.created_at <= end_date
    ).all()
    
    # Group by action
    summary = {}
    for log in logs:
        action = log.action
        if action not in summary:
            summary[action] = 0
        summary[action] += 1
    
    return summary


# SECTION 11: Benchmarking Dashboard
class BenchmarkingItem(BaseModel):
    benchmark_type: str
    benchmark_name: str
    project_value: float
    benchmark_value: float
    variance_percentage: float


@router.get("/benchmarking/{organization_id}", response_model=List[BenchmarkingItem])
async def get_benchmarking(
    organization_id: str,
    project_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get benchmarking data"""
    
    query = db.query(BenchmarkingData).filter(
        BenchmarkingData.organization_id == uuid.UUID(organization_id)
    )
    
    if project_id:
        query = query.filter(BenchmarkingData.project_id == uuid.UUID(project_id))
    
    benchmarks = query.all()
    
    return [
        BenchmarkingItem(
            benchmark_type=b.benchmark_type,
            benchmark_name=b.benchmark_name,
            project_value=float(b.project_value or 0),
            benchmark_value=float(b.benchmark_value or 0),
            variance_percentage=float(b.variance_percentage or 0)
        )
        for b in benchmarks
    ]


# SECTION 12: Export Analytics
class ExportRequest(BaseModel):
    organization_id: str
    tab: str
    filters: dict
    data: dict


@router.post("/export/{format}")
async def export_analytics(
    format: str,
    export_request: ExportRequest,
    db: Session = Depends(get_db)
):
    """Export analytics data in PDF, Excel, or CSV format"""
    
    if format not in ['pdf', 'excel', 'csv']:
        raise HTTPException(status_code=400, detail="Invalid format. Use pdf, excel, or csv")
    
    # Get organization for branding
    organization = db.query(Organization).filter(
        Organization.id == uuid.UUID(export_request.organization_id)
    ).first()
    
    org_name = organization.name if organization else "Blueprint Reader"
    export_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if format == 'csv':
        # Export as CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header with branding
        writer.writerow([f"Analytics Export - {export_request.tab}"])
        writer.writerow([f"Organization: {org_name}"])
        writer.writerow([f"Export Date: {export_date}"])
        writer.writerow([])
        
        # Write data based on tab
        data = export_request.data
        tab = export_request.tab
        
        if tab == 'executive' and data.get('kpis'):
            writer.writerow(['KPI', 'Value', 'Trend'])
            for kpi in data['kpis']:
                writer.writerow([kpi.get('title'), kpi.get('value'), kpi.get('trend')])
        
        elif tab == 'cost' and data.get('costTrends'):
            writer.writerow(['Date', 'Total Cost', 'Material Cost', 'Labour Cost', 'Overhead Cost'])
            for trend in data['costTrends']:
                writer.writerow([
                    trend.get('date'),
                    trend.get('total_cost'),
                    trend.get('material_cost'),
                    trend.get('labour_cost'),
                    trend.get('overhead_cost')
                ])
        
        elif tab == 'material' and data.get('materialQuantities'):
            writer.writerow(['Material', 'Quantity', 'Unit', 'Cost'])
            for material in data['materialQuantities']:
                writer.writerow([
                    material.get('material_name'),
                    material.get('quantity'),
                    material.get('unit'),
                    material.get('cost')
                ])
        
        else:
            # Generic export for other tabs
            writer.writerow(['Data Export'])
            writer.writerow(['Tab', tab])
            writer.writerow(['Filters', str(export_request.filters)])
        
        output.seek(0)
        csv_content = output.getvalue()
        
        return Response(
            content=csv_content,
            media_type='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=analytics-{tab}-{export_date}.csv'
            }
        )
    
    elif format == 'excel':
        # For Excel, we'll return CSV for now (can be enhanced with openpyxl later)
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow([f"Analytics Export - {export_request.tab}"])
        writer.writerow([f"Organization: {org_name}"])
        writer.writerow([f"Export Date: {export_date}"])
        writer.writerow([])
        
        data = export_request.data
        tab = export_request.tab
        
        if tab == 'executive' and data.get('kpis'):
            writer.writerow(['KPI', 'Value', 'Trend'])
            for kpi in data['kpis']:
                writer.writerow([kpi.get('title'), kpi.get('value'), kpi.get('trend')])
        
        elif tab == 'cost' and data.get('costTrends'):
            writer.writerow(['Date', 'Total Cost', 'Material Cost', 'Labour Cost', 'Overhead Cost'])
            for trend in data['costTrends']:
                writer.writerow([
                    trend.get('date'),
                    trend.get('total_cost'),
                    trend.get('material_cost'),
                    trend.get('labour_cost'),
                    trend.get('overhead_cost')
                ])
        
        else:
            writer.writerow(['Data Export'])
            writer.writerow(['Tab', tab])
        
        output.seek(0)
        csv_content = output.getvalue()
        
        return Response(
            content=csv_content,
            media_type='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=analytics-{tab}-{export_date}.xlsx'
            }
        )
    
    elif format == 'pdf':
        # For PDF, we'll return a simple text-based report for now (can be enhanced with reportlab later)
        output = io.StringIO()
        
        output.write(f"ANALYTICS REPORT - {export_request.tab.upper()}\n")
        output.write(f"=" * 50 + "\n\n")
        output.write(f"Organization: {org_name}\n")
        output.write(f"Export Date: {export_date}\n")
        output.write(f"Tab: {export_request.tab}\n\n")
        output.write("-" * 50 + "\n\n")
        
        data = export_request.data
        
        if tab == 'executive' and data.get('kpis'):
            output.write("EXECUTIVE KPIs\n")
            output.write("-" * 30 + "\n")
            for kpi in data['kpis']:
                output.write(f"{kpi.get('title')}: {kpi.get('value')} (Trend: {kpi.get('trend')}%)\n")
        
        elif tab == 'cost' and data.get('costTrends'):
            output.write("COST TRENDS\n")
            output.write("-" * 30 + "\n")
            for trend in data['costTrends']:
                output.write(f"{trend.get('date')}: Total={trend.get('total_cost')}, Material={trend.get('material_cost')}\n")
        
        else:
            output.write("DATA SUMMARY\n")
            output.write("-" * 30 + "\n")
            output.write(f"Filters: {export_request.filters}\n")
        
        output.seek(0)
        pdf_content = output.getvalue()
        
        return Response(
            content=pdf_content,
            media_type='text/plain',
            headers={
                'Content-Disposition': f'attachment; filename=analytics-{tab}-{export_date}.txt'
            }
        )


# SECTION 13: Dashboard Stats
class DashboardStats(BaseModel):
    total_projects: int
    analyses_run: int
    boqs_generated: int
    total_estimated_value: int  # in paise (INR * 100) to avoid float errors
    trends: dict


@router.get("/dashboard/stats")
async def get_dashboard_stats(
    organization_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics with trends"""
    
    # Filter by organization if provided
    org_filter = {}
    if organization_id:
        try:
            org_filter = {"organization_id": uuid.UUID(organization_id)}
        except ValueError:
            pass  # Invalid UUID, ignore filter
    
    # If no organization filter, get first organization's data for demo
    if not org_filter:
        first_org = db.query(Organization).first()
        if first_org:
            org_filter = {"organization_id": first_org.id}
    
    # Calculate stats from live data
    total_projects = db.query(Project).filter_by(**org_filter).count()
    
    analyses_run = db.query(AnalysisVersion).join(Project).filter_by(**org_filter).count()
    
    # Count BOQs generated (BOQItems with analysis_version)
    boqs_generated = db.query(BOQItem).join(AnalysisVersion).join(Project).filter_by(**org_filter).count()
    
    # Calculate total estimated value (in paise to avoid float errors)
    total_estimated_value = 0
    boq_items = db.query(BOQItem).join(AnalysisVersion).join(Project).filter_by(**org_filter).all()
    
    for item in boq_items:
        total_estimated_value += int((item.amount or 0) * 100)  # Convert to paise
    
    # Calculate trends
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)
    
    # Projects this month
    if org_filter:
        projects_this_month = db.query(Project).filter(
            Project.created_at >= month_start,
            Project.organization_id == org_filter["organization_id"]
        ).count()
    else:
        projects_this_month = db.query(Project).filter(
            Project.created_at >= month_start
        ).count()
    
    # Analyses this week
    if org_filter:
        analyses_this_week = db.query(AnalysisVersion).join(Project).filter(
            AnalysisVersion.created_at >= week_start,
            Project.organization_id == org_filter["organization_id"]
        ).count()
    else:
        analyses_this_week = db.query(AnalysisVersion).filter(
            AnalysisVersion.created_at >= week_start
        ).count()
    
    # BOQs this month
    if org_filter:
        boqs_this_month = db.query(BOQItem).join(AnalysisVersion).join(Project).filter(
            AnalysisVersion.created_at >= month_start,
            Project.organization_id == org_filter["organization_id"]
        ).count()
    else:
        boqs_this_month = db.query(BOQItem).join(AnalysisVersion).filter(
            AnalysisVersion.created_at >= month_start
        ).count()
    
    return {
        "total_projects": total_projects,
        "analyses_run": analyses_run,
        "boqs_generated": boqs_generated,
        "total_estimated_value": total_estimated_value,
        "trends": {
            "projects_this_month": projects_this_month,
            "analyses_this_week": analyses_this_week,
            "boqs_this_month": boqs_this_month
        }
    }


# SECTION 14: Activity Feed
@router.get("/activity")
async def get_activity_feed(
    limit: int = Query(10, ge=1, le=100),
    project_id: Optional[str] = Query(None),
    organization_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get activity feed with recent events"""
    
    # Get activities using service
    activity_service = ActivityService(db)
    activities = activity_service.get_activities(
        limit=limit,
        project_id=project_id,
        organization_id=organization_id
    )
    
    return {
        "activities": activities,
        "count": len(activities)
    }
