-- Analytics Schema for Enterprise Analytics Module
-- This migration creates tables for KPI tracking, cost trends, material stats, team activity

-- Analytics Snapshots (for historical KPI tracking)
CREATE TABLE analytics_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL,
    period_type VARCHAR(20) NOT NULL, -- daily, weekly, monthly, yearly
    
    -- Executive KPIs
    total_projects INTEGER DEFAULT 0,
    active_projects INTEGER DEFAULT 0,
    completed_projects INTEGER DEFAULT 0,
    total_floor_area_sqft DECIMAL(15,2) DEFAULT 0,
    total_boq_value DECIMAL(18,2) DEFAULT 0,
    avg_cost_per_sqft DECIMAL(12,2) DEFAULT 0,
    avg_project_cost DECIMAL(18,2) DEFAULT 0,
    
    -- Trends
    projects_trend DECIMAL(5,2) DEFAULT 0, -- percentage change
    boq_value_trend DECIMAL(5,2) DEFAULT 0,
    cost_per_sqft_trend DECIMAL(5,2) DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(organization_id, snapshot_date, period_type)
);

-- Cost Trends
CREATE TABLE cost_trends (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    record_date DATE NOT NULL,
    
    total_cost DECIMAL(18,2) DEFAULT 0,
    material_cost DECIMAL(18,2) DEFAULT 0,
    labour_cost DECIMAL(18,2) DEFAULT 0,
    overhead_cost DECIMAL(18,2) DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Cost Breakdown by Category
CREATE TABLE cost_breakdown (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    analysis_version_id UUID REFERENCES analysis_versions(id) ON DELETE CASCADE,
    
    category VARCHAR(100) NOT NULL, -- Civil, Electrical, Plumbing, Flooring, Painting, Finishing, HVAC
    cost DECIMAL(18,2) DEFAULT 0,
    percentage DECIMAL(5,2) DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Material Statistics
CREATE TABLE material_statistics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    
    material_name VARCHAR(100) NOT NULL, -- Cement, Steel, Sand, Aggregate, Paint, Tiles
    quantity DECIMAL(15,3) DEFAULT 0,
    unit VARCHAR(50) NOT NULL, -- kg, tons, bags, sq ft, liters
    cost DECIMAL(18,2) DEFAULT 0,
    
    record_date DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Material Cost Breakdown
CREATE TABLE material_cost_breakdown (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    
    material_name VARCHAR(100) NOT NULL,
    cost DECIMAL(18,2) DEFAULT 0,
    quantity DECIMAL(15,3) DEFAULT 0,
    cost_per_unit DECIMAL(12,2) DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Regional Cost Intelligence
CREATE TABLE regional_cost_rates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    country VARCHAR(100) NOT NULL,
    state VARCHAR(100),
    city VARCHAR(100) NOT NULL,
    
    material_name VARCHAR(100) NOT NULL,
    current_rate DECIMAL(12,2) NOT NULL,
    unit VARCHAR(50) NOT NULL,
    
    trend VARCHAR(20) DEFAULT 'stable', -- increasing, decreasing, stable
    trend_percentage DECIMAL(5,2) DEFAULT 0,
    
    effective_date DATE NOT NULL,
    expiry_date DATE,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Regional Cost History
CREATE TABLE regional_cost_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    regional_rate_id UUID REFERENCES regional_cost_rates(id) ON DELETE CASCADE,
    
    rate DECIMAL(12,2) NOT NULL,
    record_date DATE NOT NULL,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- AI Analysis Quality Metrics
CREATE TABLE ai_quality_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    analysis_version_id UUID REFERENCES analysis_versions(id) ON DELETE CASCADE,
    
    total_rooms_detected INTEGER DEFAULT 0,
    high_confidence_rooms INTEGER DEFAULT 0,
    medium_confidence_rooms INTEGER DEFAULT 0,
    low_confidence_rooms INTEGER DEFAULT 0,
    
    rooms_corrected INTEGER DEFAULT 0,
    manual_corrections INTEGER DEFAULT 0,
    accuracy_rate DECIMAL(5,2) DEFAULT 0,
    
    avg_confidence_score DECIMAL(5,2) DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Room Type Correction Stats
CREATE TABLE room_type_correction_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    room_type VARCHAR(100) NOT NULL, -- Bathroom, Balcony, Corridor, Store Room, etc.
    total_detections INTEGER DEFAULT 0,
    total_corrections INTEGER DEFAULT 0,
    correction_rate DECIMAL(5,2) DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Revision Analytics
CREATE TABLE revision_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    
    from_version_id UUID REFERENCES analysis_versions(id) ON DELETE CASCADE,
    to_version_id UUID REFERENCES analysis_versions(id) ON DELETE CASCADE,
    
    area_change_sqft DECIMAL(15,2) DEFAULT 0,
    boq_change DECIMAL(18,2) DEFAULT 0,
    cost_change DECIMAL(18,2) DEFAULT 0,
    
    rooms_added INTEGER DEFAULT 0,
    rooms_deleted INTEGER DEFAULT 0,
    rooms_modified INTEGER DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Team Activity Metrics
CREATE TABLE team_activity_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    activity_date DATE NOT NULL,
    
    analyses_run INTEGER DEFAULT 0,
    reports_exported INTEGER DEFAULT 0,
    comments_added INTEGER DEFAULT 0,
    corrections_made INTEGER DEFAULT 0,
    approvals_given INTEGER DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(organization_id, user_id, activity_date)
);

-- Portfolio Analytics
CREATE TABLE portfolio_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    total_portfolio_value DECIMAL(18,2) DEFAULT 0,
    total_area_sqft DECIMAL(15,2) DEFAULT 0,
    total_buildings INTEGER DEFAULT 0,
    total_floors INTEGER DEFAULT 0,
    
    residential_count INTEGER DEFAULT 0,
    commercial_count INTEGER DEFAULT 0,
    industrial_count INTEGER DEFAULT 0,
    mixed_use_count INTEGER DEFAULT 0,
    
    snapshot_date DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(organization_id, snapshot_date)
);

-- Approval Workflow Analytics
CREATE TABLE approval_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    snapshot_date DATE NOT NULL,
    
    pending_approvals INTEGER DEFAULT 0,
    approved_reports INTEGER DEFAULT 0,
    rejected_reports INTEGER DEFAULT 0,
    avg_approval_time_hours DECIMAL(10,2) DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(organization_id, snapshot_date)
);

-- Benchmarking Data
CREATE TABLE benchmarking_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    
    benchmark_type VARCHAR(50) NOT NULL, -- cost_per_sqft, material_usage, etc.
    benchmark_name VARCHAR(100) NOT NULL, -- Regional Average, Industry Average, etc.
    
    project_value DECIMAL(18,2) DEFAULT 0,
    benchmark_value DECIMAL(18,2) DEFAULT 0,
    variance_percentage DECIMAL(5,2) DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_analytics_snapshots_org_date ON analytics_snapshots(organization_id, snapshot_date);
CREATE INDEX idx_cost_trends_org_project_date ON cost_trends(organization_id, project_id, record_date);
CREATE INDEX idx_cost_breakdown_org_project ON cost_breakdown(organization_id, project_id);
CREATE INDEX idx_material_stats_org_project ON material_statistics(organization_id, project_id);
CREATE INDEX idx_regional_rates_org_city ON regional_cost_rates(organization_id, city);
CREATE INDEX idx_ai_quality_org_project ON ai_quality_metrics(organization_id, project_id);
CREATE INDEX idx_revision_analytics_org_project ON revision_analytics(organization_id, project_id);
CREATE INDEX idx_team_activity_org_user_date ON team_activity_metrics(organization_id, user_id, activity_date);
CREATE INDEX idx_portfolio_analytics_org_date ON portfolio_analytics(organization_id, snapshot_date);
CREATE INDEX idx_approval_analytics_org_date ON approval_analytics(organization_id, snapshot_date);
