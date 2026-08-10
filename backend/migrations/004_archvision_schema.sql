-- ArchVision v2 Schema Migration
-- This migration adds missing tables and fields to align with ArchVision specification
-- Phase 1: Database Schema Migration

-- =====================================================
-- PART 1: Enhance analysis_versions table to match analysis_jobs spec
-- =====================================================

-- Add missing fields to analysis_versions to match ArchVision analysis_jobs spec
ALTER TABLE analysis_versions 
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id),
ADD COLUMN IF NOT EXISTS file_path TEXT,
ADD COLUMN IF NOT EXISTS file_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS file_type VARCHAR(20),
ADD COLUMN IF NOT EXISTS progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
ADD COLUMN IF NOT EXISTS current_stage VARCHAR(50) 
CHECK (current_stage IN ('uploading', 'preparing', 'extracting', 'detecting', 'calibrating', 'calculating', 'estimating', 'finalizing')),
ADD COLUMN IF NOT EXISTS error_message TEXT,
ADD COLUMN IF NOT EXISTS retry_of_job_id UUID REFERENCES analysis_versions(id),
ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ;

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_analysis_versions_user_id ON analysis_versions(user_id);
CREATE INDEX IF NOT EXISTS idx_analysis_versions_status_progress ON analysis_versions(status, progress);
CREATE INDEX IF NOT EXISTS idx_analysis_versions_retry_of ON analysis_versions(retry_of_job_id);

-- Update status constraint to match ArchVision spec
ALTER TABLE analysis_versions 
DROP CONSTRAINT IF EXISTS analysis_versions_status_check,
ADD CONSTRAINT analysis_versions_status_check 
CHECK (status IN ('queued', 'processing', 'completed', 'failed'));

-- =====================================================
-- PART 2: Add is_user_corrected flags to existing tables
-- =====================================================

-- Add is_user_corrected to rooms table
ALTER TABLE rooms 
ADD COLUMN IF NOT EXISTS is_user_corrected BOOLEAN DEFAULT FALSE;

-- Add is_user_corrected flag to openings table (for doors/windows)
ALTER TABLE openings 
ADD COLUMN IF NOT EXISTS is_user_corrected BOOLEAN DEFAULT FALSE;

-- =====================================================
-- PART 3: Create dimensions table (ArchVision spec)
-- =====================================================

CREATE TABLE IF NOT EXISTS dimensions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    analysis_version_id UUID NOT NULL REFERENCES analysis_versions(id) ON DELETE CASCADE,
    raw_text TEXT NOT NULL,
    value DECIMAL(12,2) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    blueprint_coordinates JSONB,
    linked_room_id UUID REFERENCES rooms(id) ON DELETE SET NULL,
    confidence DECIMAL(5,2) DEFAULT 0.0,
    is_user_corrected BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for dimensions
CREATE INDEX idx_dimensions_project_id ON dimensions(project_id);
CREATE INDEX idx_dimensions_analysis_version_id ON dimensions(analysis_version_id);
CREATE INDEX idx_dimensions_linked_room_id ON dimensions(linked_room_id);
CREATE INDEX idx_dimensions_is_user_corrected ON dimensions(is_user_corrected);

-- =====================================================
-- PART 4: Create detected_objects table (ArchVision spec)
-- =====================================================

CREATE TABLE IF NOT EXISTS detected_objects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    analysis_version_id UUID NOT NULL REFERENCES analysis_versions(id) ON DELETE CASCADE,
    object_type VARCHAR(50) NOT NULL 
    CHECK (object_type IN ('wall', 'door', 'window', 'column', 'stair', 'furniture', 'other')),
    geometry JSONB NOT NULL,
    confidence DECIMAL(5,2) DEFAULT 0.0,
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for detected_objects
CREATE INDEX idx_detected_objects_project_id ON detected_objects(project_id);
CREATE INDEX idx_detected_objects_analysis_version_id ON detected_objects(analysis_version_id);
CREATE INDEX idx_detected_objects_object_type ON detected_objects(object_type);
CREATE INDEX idx_detected_objects_confidence ON detected_objects(confidence);

-- =====================================================
-- PART 5: Create corrections table (ArchVision spec)
-- =====================================================

CREATE TABLE IF NOT EXISTS corrections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    analysis_version_id UUID NOT NULL REFERENCES analysis_versions(id) ON DELETE CASCADE,
    target_table VARCHAR(50) NOT NULL 
    CHECK (target_table IN ('rooms', 'dimensions', 'openings', 'detected_objects', 'boq_items')),
    target_id UUID NOT NULL,
    field VARCHAR(100) NOT NULL,
    original_value TEXT,
    corrected_value TEXT NOT NULL,
    corrected_at TIMESTAMPTZ DEFAULT NOW(),
    corrected_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    correction_reason TEXT,
    properties JSONB DEFAULT '{}'
);

-- Indexes for corrections
CREATE INDEX idx_corrections_project_id ON corrections(project_id);
CREATE INDEX idx_corrections_analysis_version_id ON corrections(analysis_version_id);
CREATE INDEX idx_corrections_target_table_id ON corrections(target_table, target_id);
CREATE INDEX idx_corrections_corrected_by ON corrections(corrected_by_user_id);
CREATE INDEX idx_corrections_corrected_at ON corrections(corrected_at);

-- =====================================================
-- PART 6: Create analysis_results summary table (ArchVision spec)
-- =====================================================

CREATE TABLE IF NOT EXISTS analysis_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    analysis_version_id UUID NOT NULL REFERENCES analysis_versions(id) ON DELETE CASCADE,
    
    -- Summary metrics
    total_floor_area DECIMAL(12,2),
    room_count INTEGER DEFAULT 0,
    wall_length DECIMAL(12,2) DEFAULT 0,
    door_count INTEGER DEFAULT 0,
    window_count INTEGER DEFAULT 0,
    
    -- Cost estimates
    estimated_material_cost DECIMAL(14,2) DEFAULT 0,
    estimated_total_cost DECIMAL(14,2) DEFAULT 0,
    
    -- Quality metrics
    confidence_score DECIMAL(5,2) DEFAULT 0,
    
    -- Scale calibration data
    scale_calibration JSONB DEFAULT '{}',
    
    -- Processing metadata
    processing_metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(analysis_version_id)
);

-- Indexes for analysis_results
CREATE INDEX idx_analysis_results_project_id ON analysis_results(project_id);
CREATE INDEX idx_analysis_results_analysis_version_id ON analysis_results(analysis_version_id);

-- =====================================================
-- PART 7: Add triggers for automatic analysis_results updates
-- =====================================================

-- Function to update analysis_results when rooms change
CREATE OR REPLACE FUNCTION update_analysis_results_on_room_change()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE analysis_results 
    SET 
        total_floor_area = (SELECT COALESCE(SUM(area_sqft), 0) FROM rooms WHERE analysis_version_id = NEW.analysis_version_id AND NOT is_deleted),
        room_count = (SELECT COUNT(*) FROM rooms WHERE analysis_version_id = NEW.analysis_version_id AND NOT is_deleted),
        updated_at = NOW()
    WHERE analysis_version_id = NEW.analysis_version_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for room inserts and updates
CREATE TRIGGER trigger_room_analysis_results
AFTER INSERT OR UPDATE ON rooms
FOR EACH ROW
EXECUTE FUNCTION update_analysis_results_on_room_change();

-- Trigger for room deletes
CREATE TRIGGER trigger_room_delete_analysis_results
AFTER DELETE ON rooms
FOR EACH ROW
EXECUTE FUNCTION update_analysis_results_on_room_change();

-- =====================================================
-- PART 8: Migration data from existing analysis_versions to new structure
-- =====================================================

-- Update existing analysis_versions to have proper status values
UPDATE analysis_versions 
SET status = CASE 
    WHEN status = 'completed' THEN 'completed'
    WHEN status = 'processing' THEN 'processing'
    ELSE 'queued'
END
WHERE status NOT IN ('queued', 'processing', 'completed', 'failed');

-- Set initial progress for completed jobs
UPDATE analysis_versions 
SET progress = 100, current_stage = 'finalizing'
WHERE status = 'completed' AND progress IS NULL;

-- Set initial progress for processing jobs
UPDATE analysis_versions 
SET progress = 50, current_stage = 'detecting'
WHERE status = 'processing' AND progress IS NULL;

-- Create analysis_results records for existing analysis_versions
INSERT INTO analysis_results (project_id, analysis_version_id, total_floor_area, room_count, wall_length, door_count, window_count, estimated_material_cost, estimated_total_cost, confidence_score, scale_calibration, processing_metadata)
SELECT 
    av.project_id,
    av.id,
    av.total_area_sqft,
    av.room_count,
    0 as wall_length, -- Will need to be calculated from geometry
    av.door_count,
    av.window_count,
    0 as estimated_material_cost, -- Will need to be calculated from BOQ
    0 as estimated_total_cost, -- Will need to be calculated from BOQ
    av.confidence_score,
    '{}'::jsonb as scale_calibration,
    '{}'::jsonb as processing_metadata
FROM analysis_versions av
WHERE NOT EXISTS (SELECT 1 FROM analysis_results ar WHERE ar.analysis_version_id = av.id);

-- =====================================================
-- PART 9: Add comments for documentation
-- =====================================================

COMMENT ON TABLE analysis_versions IS 'Enhanced to match ArchVision analysis_jobs spec with progress tracking and retry support';
COMMENT ON COLUMN analysis_versions.user_id IS 'User who initiated the analysis job';
COMMENT ON COLUMN analysis_versions.file_path IS 'Storage path for the blueprint file';
COMMENT ON COLUMN analysis_versions.file_name IS 'Original filename of the blueprint';
COMMENT ON COLUMN analysis_versions.file_type IS 'File type: pdf, image, dxf, ifc';
COMMENT ON COLUMN analysis_versions.progress IS 'Progress percentage (0-100) for Realtime updates';
COMMENT ON COLUMN analysis_versions.current_stage IS 'Current processing stage: uploading, preparing, extracting, detecting, calibrating, calculating, estimating, finalizing';
COMMENT ON COLUMN analysis_versions.error_message IS 'User-safe error message for failed jobs';
COMMENT ON COLUMN analysis_versions.retry_of_job_id IS 'References original job if this is a retry';
COMMENT ON COLUMN analysis_versions.started_at IS 'Timestamp when job processing started';

COMMENT ON TABLE dimensions IS 'Extracted dimensions from blueprints with OCR and vision';
COMMENT ON COLUMN dimensions.blueprint_coordinates IS 'Geometry coordinates in normalized (0-1) space';
COMMENT ON COLUMN dimensions.is_user_corrected IS 'Flag indicating if dimension was manually corrected by user';

COMMENT ON TABLE detected_objects IS 'AI-detected objects: walls, doors, windows, columns, stairs, furniture';
COMMENT ON COLUMN detected_objects.geometry IS 'Geometry coordinates in normalized (0-1) space';
COMMENT ON COLUMN detected_objects.object_type IS 'Type of detected object';
COMMENT ON COLUMN detected_objects.properties IS 'Additional properties and metadata for the detected object';

COMMENT ON TABLE corrections IS 'Audit trail for user corrections with automatic recalculation triggers';
COMMENT ON COLUMN corrections.target_table IS 'Table containing the corrected entity';
COMMENT ON COLUMN corrections.target_id IS 'ID of the corrected entity';
COMMENT ON COLUMN corrections.field IS 'Field name that was corrected';
COMMENT ON COLUMN corrections.original_value IS 'Original value before correction';
COMMENT ON COLUMN corrections.corrected_value IS 'New value after correction';
COMMENT ON COLUMN corrections.properties IS 'Additional properties and metadata for the correction';

COMMENT ON TABLE analysis_results IS 'Summary metrics and calculations for each analysis version';
COMMENT ON COLUMN analysis_results.scale_calibration IS 'Scale calibration data and confidence metrics';
COMMENT ON COLUMN analysis_results.processing_metadata IS 'Processing metadata, timing, and model information';

-- =====================================================
-- END OF MIGRATION
-- =====================================================