-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- CREATE EXTENSION IF NOT EXISTS "pgvector"; -- Optional - skip if not installed
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Organizations (Multi-tenancy root)
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    logo_url TEXT,
    brand_color VARCHAR(7),
    plan_tier VARCHAR(50) DEFAULT 'starter',
    max_users INTEGER DEFAULT 5,
    max_projects INTEGER DEFAULT 10,
    max_storage_gb INTEGER DEFAULT 10,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- Users (linked to Clerk)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clerk_user_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- Organization Memberships
CREATE TABLE organization_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL DEFAULT 'viewer',
    invited_by UUID REFERENCES users(id),
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(organization_id, user_id),
    CONSTRAINT valid_role CHECK (role IN ('admin', 'project_manager', 'viewer'))
);

-- Projects
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50),
    client_name VARCHAR(255),
    location_country VARCHAR(100),
    location_state VARCHAR(100),
    location_city VARCHAR(100),
    building_type VARCHAR(100),
    unit_system VARCHAR(20) DEFAULT 'imperial',
    status VARCHAR(50) DEFAULT 'draft',
    settings JSONB DEFAULT '{}',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- Project Teams
CREATE TABLE project_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'viewer',
    added_by UUID REFERENCES users(id),
    added_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(project_id, user_id)
);

-- Blueprint Files
CREATE TABLE blueprint_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    file_type VARCHAR(20) NOT NULL,
    file_size BIGINT NOT NULL,
    storage_path TEXT NOT NULL,
    storage_bucket VARCHAR(255),
    checksum VARCHAR(64),
    uploaded_by UUID REFERENCES users(id),
    uploaded_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- Analysis Versions (Revisions)
CREATE TABLE analysis_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    blueprint_file_id UUID REFERENCES blueprint_files(id),
    version_number INTEGER NOT NULL,
    name VARCHAR(255),
    description TEXT,
    status VARCHAR(50) DEFAULT 'processing',
    total_area_sqft DECIMAL(12,2),
    total_area_sqm DECIMAL(12,2),
    room_count INTEGER,
    floor_count INTEGER,
    door_count INTEGER,
    window_count INTEGER,
    confidence_score DECIMAL(5,2),
    processing_time_seconds INTEGER,
    ai_model_used VARCHAR(100),
    settings JSONB DEFAULT '{}',
    raw_result JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    UNIQUE(project_id, version_number)
);

-- Rooms
CREATE TABLE rooms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_version_id UUID NOT NULL REFERENCES analysis_versions(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    room_type VARCHAR(100),
    floor_number INTEGER DEFAULT 1,
    area_sqft DECIMAL(12,2),
    area_sqm DECIMAL(12,2),
    width_ft DECIMAL(10,2),
    height_ft DECIMAL(10,2),
    width_m DECIMAL(10,2),
    height_m DECIMAL(10,2),
    confidence_score DECIMAL(5,2),
    source VARCHAR(50),
    polygon_coordinates JSONB,
    centroid_x DECIMAL(12,2),
    centroid_y DECIMAL(12,2),
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Openings (Doors/Windows)
CREATE TABLE openings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    room_id UUID REFERENCES rooms(id) ON DELETE CASCADE,
    analysis_version_id UUID NOT NULL REFERENCES analysis_versions(id) ON DELETE CASCADE,
    opening_type VARCHAR(50) NOT NULL,
    width_ft DECIMAL(10,2),
    height_ft DECIMAL(10,2),
    width_m DECIMAL(10,2),
    height_m DECIMAL(10,2),
    position_x DECIMAL(12,2),
    position_y DECIMAL(12,2),
    confidence_score DECIMAL(5,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Rate Cards (Regional pricing) - MOVED BEFORE boq_items
CREATE TABLE rate_cards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    country VARCHAR(100),
    state VARCHAR(100),
    city VARCHAR(100),
    effective_date DATE NOT NULL,
    expiry_date DATE,
    is_default BOOLEAN DEFAULT FALSE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Rate Card Items
CREATE TABLE rate_card_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rate_card_id UUID NOT NULL REFERENCES rate_cards(id) ON DELETE CASCADE,
    item_code VARCHAR(100),
    category VARCHAR(255),
    description TEXT NOT NULL,
    unit VARCHAR(50) NOT NULL,
    rate DECIMAL(12,2) NOT NULL,
    material_cost DECIMAL(12,2),
    labour_cost DECIMAL(12,2),
    overhead_cost DECIMAL(12,2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- BOQ Items - MOVED AFTER rate_cards
CREATE TABLE boq_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_version_id UUID NOT NULL REFERENCES analysis_versions(id) ON DELETE CASCADE,
    category VARCHAR(255) NOT NULL,
    item_code VARCHAR(100),
    description TEXT NOT NULL,
    unit VARCHAR(50) NOT NULL,
    quantity DECIMAL(12,3),
    rate DECIMAL(12,2),
    amount DECIMAL(14,2),
    source VARCHAR(50),
    rate_card_id UUID REFERENCES rate_cards(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Material Rate History (for trends)
CREATE TABLE material_rate_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    material_name VARCHAR(255) NOT NULL,
    country VARCHAR(100),
    state VARCHAR(100),
    city VARCHAR(100),
    rate DECIMAL(12,2) NOT NULL,
    unit VARCHAR(50) NOT NULL,
    recorded_at DATE NOT NULL,
    source VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Comments
CREATE TABLE comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    analysis_version_id UUID REFERENCES analysis_versions(id) ON DELETE CASCADE,
    room_id UUID REFERENCES rooms(id) ON DELETE CASCADE,
    boq_item_id UUID REFERENCES boq_items(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    content TEXT NOT NULL,
    parent_id UUID REFERENCES comments(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- Approvals
CREATE TABLE approvals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    analysis_version_id UUID NOT NULL REFERENCES analysis_versions(id) ON DELETE CASCADE,
    approver_id UUID NOT NULL REFERENCES users(id),
    status VARCHAR(50) DEFAULT 'pending',
    comments TEXT,
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit Logs
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Exports
CREATE TABLE exports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    analysis_version_id UUID NOT NULL REFERENCES analysis_versions(id) ON DELETE CASCADE,
    export_type VARCHAR(50) NOT NULL,
    format VARCHAR(50),
    status VARCHAR(50) DEFAULT 'processing',
    file_path TEXT,
    file_size BIGINT,
    exported_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Scale Calibrations
CREATE TABLE scale_calibrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_version_id UUID NOT NULL REFERENCES analysis_versions(id) ON DELETE CASCADE,
    point1_x DECIMAL(12,2),
    point1_y DECIMAL(12,2),
    point2_x DECIMAL(12,2),
    point2_y DECIMAL(12,2),
    known_distance DECIMAL(12,2) NOT NULL,
    known_unit VARCHAR(20) NOT NULL,
    calculated_scale DECIMAL(12,6),
    reference_type VARCHAR(50),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_organizations_slug ON organizations(slug);
CREATE INDEX idx_users_clerk_id ON users(clerk_user_id);
CREATE INDEX idx_organization_members_org ON organization_members(organization_id);
CREATE INDEX idx_organization_members_user ON organization_members(user_id);
CREATE INDEX idx_projects_org ON projects(organization_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_blueprint_files_project ON blueprint_files(project_id);
CREATE INDEX idx_analysis_versions_project ON analysis_versions(project_id);
CREATE INDEX idx_analysis_versions_status ON analysis_versions(status);
CREATE INDEX idx_rooms_analysis ON rooms(analysis_version_id);
CREATE INDEX idx_boq_items_analysis ON boq_items(analysis_version_id);
CREATE INDEX idx_rate_cards_org ON rate_cards(organization_id);
CREATE INDEX idx_rate_cards_location ON rate_cards(country, state, city);
CREATE INDEX idx_comments_project ON comments(project_id);
CREATE INDEX idx_audit_logs_org ON audit_logs(organization_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);
CREATE INDEX idx_material_rate_history_material ON material_rate_history(material_name);
CREATE INDEX idx_material_rate_history_location ON material_rate_history(country, state, city);
CREATE INDEX idx_material_rate_history_date ON material_rate_history(recorded_at);

-- Row Level Security Policies
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE analysis_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE rooms ENABLE ROW LEVEL SECURITY;
ALTER TABLE boq_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE rate_cards ENABLE ROW LEVEL SECURITY;
ALTER TABLE comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- RLS Policy for organizations
CREATE POLICY org_isolation ON organizations
    FOR ALL
    USING (
        id IN (
            SELECT organization_id 
            FROM organization_members 
            WHERE user_id = (SELECT id FROM users WHERE clerk_user_id = current_setting('app.clerk_user_id'))
        )
    );

-- RLS Policy for projects
CREATE POLICY project_isolation ON projects
    FOR ALL
    USING (
        organization_id IN (
            SELECT organization_id 
            FROM organization_members 
            WHERE user_id = (SELECT id FROM users WHERE clerk_user_id = current_setting('app.clerk_user_id'))
        )
    );
