# Phase 1 Implementation Guide: Database Schema Migration

## Overview

This guide details the completion of **Phase 1: Database Schema Migration** for ArchVision v2 compliance. All migration files, model updates, and API endpoints have been created successfully.

## What Was Completed

### 1. Migration SQL File Created
**File**: `backend/migrations/004_archvision_schema.sql`

This migration includes:
- ✅ Enhanced `analysis_versions` table with ArchVision fields
- ✅ Added `is_user_corrected` flags to `rooms` and `openings` tables  
- ✅ Created `dimensions` table for extracted measurements
- ✅ Created `detected_objects` table for AI-detected elements
- ✅ Created `corrections` table for audit trail
- ✅ Created `analysis_results` summary table
- ✅ Added automatic triggers for analysis results updates
- ✅ Data migration for existing records
- ✅ Comprehensive indexing for performance
- ✅ Documentation comments

### 2. Backend Models Updated
**Files Modified**:
- `backend/models/analysis.py` - Enhanced with new models and fields
- `backend/models/opening.py` - Created new model file
- `backend/models/__init__.py` - Updated imports

**New Models Added**:
- `Dimension` - For extracted blueprint dimensions
- `DetectedObject` - For AI-detected elements (walls, doors, windows, etc.)
- `Correction` - For user correction audit trail
- `AnalysisResult` - For summary metrics and calculations

**Enhanced Models**:
- `AnalysisVersion` - Added progress tracking, retry support, user_id
- `Room` - Added `is_user_corrected` flag
- `Opening` - Added `is_user_corrected` flag

### 3. New API Endpoints Created
**Files Created**:
- `backend/api/dimensions.py` - CRUD operations for dimensions
- `backend/api/detected_objects.py` - CRUD operations for detected objects
- `backend/api/corrections_v2.py` - ArchVision-compliant correction system
- `backend/api/analysis_results.py` - Analysis results management

**API Routes Added**:
- `/api/v1/dimensions/*` - Dimension management
- `/api/v1/detected-objects/*` - Detected object management
- `/api/v1/corrections-v2/*` - Correction audit trail
- `/api/v1/analysis-results/*` - Analysis results management

### 4. Main Application Updated
**File**: `backend/main.py`
- ✅ Added imports for new API routers
- ✅ Registered new API routes with `/api/v1` prefix

## How to Apply the Migration

### Step 1: Backup Your Database
Before running any migration, always backup your Supabase database:

```bash
# Using Supabase CLI
supabase db dump -f backup_before_phase1.sql

# Or via Supabase Dashboard
# Dashboard → Database → Backups → Create Backup
```

### Step 2: Apply the Migration
Choose one of the following methods:

#### Option A: Via Supabase Dashboard (Recommended)
1. Go to Supabase Dashboard → Your Project → SQL Editor
2. Copy the contents of `backend/migrations/004_archvision_schema.sql`
3. Paste into the SQL Editor
4. Click "Run" to execute the migration
5. Review the output for any errors

#### Option B: Via Supabase CLI
```bash
cd /Users/swarajdeshmukh4249gmail.com/Desktop/blueprint-reader
supabase db push
```

#### Option C: Via psql Command Line
```bash
psql -h db.xxx.supabase.co -U postgres -d postgres -f backend/migrations/004_archvision_schema.sql
```

### Step 3: Verify the Migration
Run these verification queries in Supabase SQL Editor:

```sql
-- Check new tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('dimensions', 'detected_objects', 'corrections', 'analysis_results');

-- Check new columns exist in analysis_versions
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'analysis_versions' 
AND column_name IN ('user_id', 'file_path', 'progress', 'current_stage', 'retry_of_job_id');

-- Check is_user_corrected flags
SELECT column_name 
FROM information_schema.columns 
WHERE table_name IN ('rooms', 'openings') 
AND column_name = 'is_user_corrected';

-- Check triggers exist
SELECT trigger_name 
FROM information_schema.triggers 
WHERE trigger_name LIKE '%analysis_results%';
```

### Step 4: Update Backend Dependencies
Ensure your backend has the required dependencies:

```bash
cd /Users/swarajdeshmukh4249gmail.com/Desktop/blueprint-reader/backend
../venv/bin/pip install -r requirements.txt
```

### Step 5: Restart Backend Services
```bash
# Stop any running backend services
# Then restart
cd /Users/swarajdeshmukh4249gmail.com/Desktop/blueprint-reader/backend
../venv/bin/python -m uvicorn main:app --reload --port 8000
```

### Step 6: Test New API Endpoints
Test the new endpoints to ensure they work correctly:

```bash
# Test dimensions endpoint
curl -X GET http://localhost:8000/api/v1/dimensions/analysis/{analysis_version_id}

# Test detected objects endpoint  
curl -X GET http://localhost:8000/api/v1/detected-objects/analysis/{analysis_version_id}

# Test corrections endpoint
curl -X GET http://localhost:8000/api/v1/corrections-v2/analysis/{analysis_version_id}

# Test analysis results endpoint
curl -X GET http://localhost:8000/api/v1/analysis-results/analysis/{analysis_version_id}
```

## Data Migration Notes

### Existing Data Handling
The migration includes automatic data migration:
- ✅ Existing `analysis_versions` records get proper status values
- ✅ Completed jobs get `progress = 100` and `current_stage = 'finalizing'`
- ✅ Processing jobs get `progress = 50` and `current_stage = 'detecting'`
- ✅ `analysis_results` records are created for existing analysis versions

### Backward Compatibility
The migration maintains backward compatibility:
- ✅ Existing API endpoints continue to work
- ✅ New fields are nullable where appropriate
- ✅ Existing data is preserved and enhanced
- ✅ No breaking changes to existing functionality

## Model Changes Summary

### AnalysisVersion Model
**New Fields**:
- `user_id` - User who initiated the analysis
- `file_path` - Storage path for blueprint file
- `file_name` - Original filename
- `file_type` - File type (pdf, image, dxf, ifc)
- `progress` - Progress percentage (0-100)
- `current_stage` - Current processing stage
- `error_message` - User-safe error message
- `retry_of_job_id` - Reference to original job if retry
- `started_at` - Processing start timestamp

**New Constraints**:
- Progress range check (0-100)
- Status validation (queued, processing, completed, failed)
- Stage validation (uploading, preparing, extracting, detecting, calibrating, calculating, estimating, finalizing)

### Room Model
**New Fields**:
- `is_user_corrected` - Boolean flag for manual corrections

### Opening Model  
**New Fields**:
- `is_user_corrected` - Boolean flag for manual corrections

## API Endpoint Documentation

### Dimensions API
- `POST /api/v1/dimensions/` - Create dimension
- `GET /api/v1/dimensions/{id}` - Get specific dimension
- `GET /api/v1/dimensions/analysis/{version_id}` - List by analysis
- `PUT /api/v1/dimensions/{id}` - Update dimension
- `DELETE /api/v1/dimensions/{id}` - Delete dimension

### Detected Objects API
- `POST /api/v1/detected-objects/` - Create detected object
- `GET /api/v1/detected-objects/{id}` - Get specific object
- `GET /api/v1/detected-objects/analysis/{version_id}` - List by analysis
- `PUT /api/v1/detected-objects/{id}` - Update object
- `DELETE /api/v1/detected-objects/{id}` - Delete object

**Note**: The `metadata` field has been renamed to `properties` to avoid conflicts with SQLAlchemy's reserved attribute names.

### Corrections V2 API
- `POST /api/v1/corrections-v2/` - Create correction with audit trail
- `GET /api/v1/corrections-v2/{id}` - Get specific correction
- `GET /api/v1/corrections-v2/analysis/{version_id}` - List by analysis
- `GET /api/v1/corrections-v2/target/{table}/{id}` - List by target entity

**Note**: The `metadata` field has been renamed to `properties` to avoid conflicts with SQLAlchemy's reserved attribute names.

### Analysis Results API
- `POST /api/v1/analysis-results/` - Create analysis result
- `GET /api/v1/analysis-results/{id}` - Get specific result
- `GET /api/v1/analysis-results/analysis/{version_id}` - Get by analysis version
- `PUT /api/v1/analysis-results/{id}` - Update result
- `DELETE /api/v1/analysis-results/{id}` - Delete result

## Rollback Plan

If you need to rollback the migration:

```sql
-- Drop new tables
DROP TABLE IF EXISTS corrections CASCADE;
DROP TABLE IF EXISTS analysis_results CASCADE;
DROP TABLE IF EXISTS detected_objects CASCADE;
DROP TABLE IF EXISTS dimensions CASCADE;

-- Remove new columns from analysis_versions
ALTER TABLE analysis_versions 
DROP COLUMN IF EXISTS user_id,
DROP COLUMN IF EXISTS file_path,
DROP COLUMN IF EXISTS file_name,
DROP COLUMN IF EXISTS file_type,
DROP COLUMN IF EXISTS progress,
DROP COLUMN IF EXISTS current_stage,
DROP COLUMN IF EXISTS error_message,
DROP COLUMN IF EXISTS retry_of_job_id,
DROP COLUMN IF EXISTS started_at;

-- Remove is_user_corrected flags
ALTER TABLE rooms DROP COLUMN IF EXISTS is_user_corrected;
ALTER TABLE openings DROP COLUMN IF EXISTS is_user_corrected;

-- Drop triggers
DROP TRIGGER IF EXISTS trigger_room_analysis_results ON rooms;
DROP TRIGGER IF EXISTS trigger_room_delete_analysis_results ON rooms;
DROP FUNCTION IF EXISTS update_analysis_results_on_room_change();

-- Note: If you need to rollback the metadata->properties rename:
-- ALTER TABLE detected_objects RENAME COLUMN properties TO metadata;
-- ALTER TABLE corrections RENAME COLUMN properties TO metadata;
```

## Next Steps

After completing Phase 1, you can proceed to:

### Phase 2: Realtime Implementation
- Replace frontend polling with Supabase Realtime subscriptions
- Implement stage-based progress updates in worker
- Add `current_stage` and `progress` field updates

### Phase 3: Geometry Normalization
- Verify current coordinate system
- Implement normalized coordinate conversion (0-1 range)
- Update geometry storage to use normalized coordinates
- Test click-to-highlight functionality

## Troubleshooting

### Migration Fails
- Check for syntax errors in the SQL
- Ensure you have sufficient permissions
- Verify database connection
- Check Supabase logs for detailed error messages

### Backend Won't Start
- Verify all dependencies are installed
- Check that models import correctly
- Review environment variables
- Check for import errors in new files

### API Endpoints Return 404
- Verify routes are registered in main.py
- Check router prefixes are correct
- Ensure FastAPI is running
- Review API logs for routing issues

## Support

For issues or questions:
1. Check the ArchVision mapping document: `ARCHITECTURE_MAPPING.md`
2. Review migration SQL comments for detailed explanations
3. Check Supabase logs for database-related issues
4. Review FastAPI logs for API-related issues

## Summary

Phase 1 database schema migration is **complete and ready for deployment**. All necessary files have been created, models updated, and API endpoints implemented. The migration maintains backward compatibility while adding all required ArchVision v2 database components.

**Status**: ✅ **READY FOR DEPLOYMENT**