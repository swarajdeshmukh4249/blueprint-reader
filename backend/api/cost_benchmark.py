from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timedelta
import uuid

from models import get_db
from models.cost_benchmark import CostBenchmark, IndustryCostData
from models.project import Project
from models.blueprint_file import BlueprintFile

router = APIRouter(prefix="/cost-benchmark", tags=["cost-benchmark"])

# Pydantic models
class CostBenchmarkCreate(BaseModel):
    project_id: str
    category: str
    metric_name: str
    your_value: float
    your_unit: Optional[str] = None
    benchmark_value: float
    benchmark_unit: Optional[str] = None
    benchmark_source: Optional[str] = None
    region: Optional[str] = None
    building_type: Optional[str] = None
    project_size_category: Optional[str] = None

class CostBenchmarkResponse(BaseModel):
    id: str
    project_id: str
    category: str
    metric_name: str
    your_value: float
    your_unit: Optional[str]
    benchmark_value: float
    benchmark_unit: Optional[str]
    benchmark_source: Optional[str]
    variance_percentage: Optional[float]
    variance_status: Optional[str]
    region: Optional[str]
    building_type: Optional[str]
    project_size_category: Optional[str]
    created_at: datetime

class IndustryCostDataResponse(BaseModel):
    id: str
    category: str
    metric_name: str
    benchmark_value: float
    unit: Optional[str]
    min_value: Optional[float]
    max_value: Optional[float]
    percentile_25: Optional[float]
    percentile_75: Optional[float]
    region: Optional[str]
    building_type: Optional[str]
    project_size: Optional[str]
    source: Optional[str]
    source_year: Optional[int]

@router.post("/", response_model=CostBenchmarkResponse)
async def create_cost_benchmark(
    benchmark_data: CostBenchmarkCreate,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Create a cost benchmark entry for a project"""
    
    # Optional authentication
    user_id = None
    if authorization:
        try:
            from auth.clerk import verify_jwt
            user = verify_jwt(authorization.replace("Bearer ", ""))
            user_id = user.get('id')
        except:
            pass  # Allow request to proceed even if auth fails
    
    # Validate project exists
    try:
        project_uuid = uuid.UUID(benchmark_data.project_id)
        project = db.query(Project).filter(Project.id == project_uuid).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project ID")
    
    # Calculate variance
    variance_percentage = None
    variance_status = None
    if benchmark_data.benchmark_value != 0:
        variance_percentage = ((benchmark_data.your_value - benchmark_data.benchmark_value) / benchmark_data.benchmark_value) * 100
        
        # Determine status
        if abs(variance_percentage) <= 10:
            variance_status = "within_range"
        elif variance_percentage > 10:
            variance_status = "above"
        else:
            variance_status = "below"
    
    # Create benchmark record
    benchmark = CostBenchmark(
        project_id=project_uuid,
        category=benchmark_data.category,
        metric_name=benchmark_data.metric_name,
        your_value=benchmark_data.your_value,
        your_unit=benchmark_data.your_unit,
        benchmark_value=benchmark_data.benchmark_value,
        benchmark_unit=benchmark_data.benchmark_unit,
        benchmark_source=benchmark_data.benchmark_source,
        variance_percentage=variance_percentage,
        variance_status=variance_status,
        region=benchmark_data.region,
        building_type=benchmark_data.building_type,
        project_size_category=benchmark_data.project_size_category
    )
    
    db.add(benchmark)
    db.commit()
    db.refresh(benchmark)
    
    return CostBenchmarkResponse(
        id=str(benchmark.id),
        project_id=str(benchmark.project_id),
        category=benchmark.category,
        metric_name=benchmark.metric_name,
        your_value=benchmark.your_value,
        your_unit=benchmark.your_unit,
        benchmark_value=benchmark.benchmark_value,
        benchmark_unit=benchmark.benchmark_unit,
        benchmark_source=benchmark.benchmark_source,
        variance_percentage=benchmark.variance_percentage,
        variance_status=benchmark.variance_status,
        region=benchmark.region,
        building_type=benchmark.building_type,
        project_size_category=benchmark.project_size_category,
        created_at=benchmark.created_at
    )

@router.get("/project/{project_id}", response_model=List[CostBenchmarkResponse])
async def list_project_benchmarks(
    project_id: str,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """List all cost benchmarks for a project"""
    
    # Optional authentication
    if authorization:
        try:
            from auth.clerk import verify_jwt
            verify_jwt(authorization.replace("Bearer ", ""))
        except:
            pass  # Allow request to proceed even if auth fails
    
    try:
        project_uuid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project ID")
    
    benchmarks = db.query(CostBenchmark).filter(
        CostBenchmark.project_id == project_uuid
    ).order_by(CostBenchmark.created_at.desc()).all()
    
    return [
        CostBenchmarkResponse(
            id=str(b.id),
            project_id=str(b.project_id),
            category=b.category,
            metric_name=b.metric_name,
            your_value=b.your_value,
            your_unit=b.your_unit,
            benchmark_value=b.benchmark_value,
            benchmark_unit=b.benchmark_unit,
            benchmark_source=b.benchmark_source,
            variance_percentage=b.variance_percentage,
            variance_status=b.variance_status,
            region=b.region,
            building_type=b.building_type,
            project_size_category=b.project_size_category,
            created_at=b.created_at
        )
        for b in benchmarks
    ]

@router.get("/industry-data", response_model=List[IndustryCostDataResponse])
async def list_industry_data(
    category: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    building_type: Optional[str] = Query(None),
    project_size: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """List industry cost benchmark data with optional filters"""
    
    # Optional authentication
    if authorization:
        try:
            from auth.clerk import verify_jwt
            verify_jwt(authorization.replace("Bearer ", ""))
        except:
            pass  # Allow request to proceed even if auth fails
    
    query = db.query(IndustryCostData)
    
    if category:
        query = query.filter(IndustryCostData.category == category)
    if region:
        query = query.filter(IndustryCostData.region == region)
    if building_type:
        query = query.filter(IndustryCostData.building_type == building_type)
    if project_size:
        query = query.filter(IndustryCostData.project_size == project_size)
    
    data = query.order_by(IndustryCostData.category, IndustryCostData.metric_name).all()
    
    return [
        IndustryCostDataResponse(
            id=str(d.id),
            category=d.category,
            metric_name=d.metric_name,
            benchmark_value=d.benchmark_value,
            unit=d.unit,
            min_value=d.min_value,
            max_value=d.max_value,
            percentile_25=d.percentile_25,
            percentile_75=d.percentile_75,
            region=d.region,
            building_type=d.building_type,
            project_size=d.project_size,
            source=d.source,
            source_year=d.source_year
        )
        for d in data
    ]

@router.post("/industry-data", response_model=IndustryCostDataResponse)
async def create_industry_data(
    data: dict,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Create industry cost benchmark data (admin function)"""
    
    # Optional authentication
    if authorization:
        try:
            from auth.clerk import verify_jwt
            verify_jwt(authorization.replace("Bearer ", ""))
        except:
            pass  # Allow request to proceed even if auth fails
    
    industry_data = IndustryCostData(
        category=data.get('category'),
        metric_name=data.get('metric_name'),
        benchmark_value=data.get('benchmark_value'),
        unit=data.get('unit'),
        min_value=data.get('min_value'),
        max_value=data.get('max_value'),
        percentile_25=data.get('percentile_25'),
        percentile_75=data.get('percentile_75'),
        region=data.get('region'),
        building_type=data.get('building_type'),
        project_size=data.get('project_size'),
        source=data.get('source'),
        source_year=data.get('source_year')
    )
    
    db.add(industry_data)
    db.commit()
    db.refresh(industry_data)
    
    return IndustryCostDataResponse(
        id=str(industry_data.id),
        category=industry_data.category,
        metric_name=industry_data.metric_name,
        benchmark_value=industry_data.benchmark_value,
        unit=industry_data.unit,
        min_value=industry_data.min_value,
        max_value=industry_data.max_value,
        percentile_25=industry_data.percentile_25,
        percentile_75=industry_data.percentile_75,
        region=industry_data.region,
        building_type=industry_data.building_type,
        project_size=industry_data.project_size,
        source=industry_data.source,
        source_year=industry_data.source_year
    )

@router.delete("/{benchmark_id}")
async def delete_benchmark(
    benchmark_id: str,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Delete a cost benchmark"""
    
    # Optional authentication
    if authorization:
        try:
            from auth.clerk import verify_jwt
            verify_jwt(authorization.replace("Bearer ", ""))
        except:
            pass  # Allow request to proceed even if auth fails
    
    try:
        benchmark_uuid = uuid.UUID(benchmark_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid benchmark ID")
    
    benchmark = db.query(CostBenchmark).filter(CostBenchmark.id == benchmark_uuid).first()
    
    if not benchmark:
        raise HTTPException(status_code=404, detail="Benchmark not found")
    
    db.delete(benchmark)
    db.commit()
    
    return {"message": "Benchmark deleted successfully"}

@router.get("/compare/{project_id}")
async def compare_project_to_industry(
    project_id: str,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Compare a project's costs against industry benchmarks"""
    
    # Optional authentication
    if authorization:
        try:
            from auth.clerk import verify_jwt
            verify_jwt(authorization.replace("Bearer ", ""))
        except:
            pass  # Allow request to proceed even if auth fails
    
    try:
        project_uuid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project ID")
    
    project = db.query(Project).filter(Project.id == project_uuid).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get project's analyzed files to extract actual data
    files = db.query(BlueprintFile).filter(
        BlueprintFile.project_id == project_uuid,
        BlueprintFile.status == 'analyzed'
    ).all()
    
    if not files:
        raise HTTPException(status_code=404, detail="No analyzed files found for this project")
    
    # Calculate project metrics from files
    total_area = sum(f.total_area or 0 for f in files)
    total_boq = 0
    for f in files:
        if f.analysis_result and f.analysis_result.get('boq'):
            total_boq += sum(item.get('amount', 0) or 0 for item in f.analysis_result['boq'])
    
    cost_per_sqft = total_boq / total_area if total_area > 0 else 0
    
    # Get relevant industry benchmarks
    industry_data = db.query(IndustryCostData).filter(
        IndustryCostData.region == project.location_state,
        IndustryCostData.building_type == project.building_type
    ).all()
    
    # Build comparison
    comparison = {
        "project_id": project_id,
        "project_name": project.name,
        "metrics": []
    }
    
    # Cost per sq ft comparison
    cost_benchmark = next((d for d in industry_data if d.category == "cost_per_sqft"), None)
    if cost_benchmark:
        variance = ((cost_per_sqft - cost_benchmark.benchmark_value) / cost_benchmark.benchmark_value) * 100 if cost_benchmark.benchmark_value != 0 else 0
        comparison["metrics"].append({
            "metric": "Cost per Sq Ft",
            "your_value": cost_per_sqft,
            "benchmark_value": cost_benchmark.benchmark_value,
            "variance_percentage": variance,
            "status": "above" if variance > 10 else "below" if variance < -10 else "within_range"
        })
    
    # Add more metrics from existing benchmarks
    existing_benchmarks = db.query(CostBenchmark).filter(
        CostBenchmark.project_id == project_uuid
    ).all()
    
    for b in existing_benchmarks:
        comparison["metrics"].append({
            "metric": b.metric_name,
            "your_value": b.your_value,
            "benchmark_value": b.benchmark_value,
            "variance_percentage": b.variance_percentage,
            "status": b.variance_status
        })
    
    return comparison
