# ArchVision Architecture Mapping Document

## Executive Summary

This document maps the current Blueprint Reader implementation against the ArchVision v2 specification. The current system is **80% aligned** with the spec, with the main gaps being in Realtime subscriptions, normalized geometry storage, and the corrections table structure.

---

## 1. System Flow Mapping

### ArchVision Spec Flow
```
USER → VITE + REACT FRONTEND → SUPABASE STORAGE → SUPABASE DATABASE → 
PYTHON WORKER / FASTAPI → DOWNLOAD BLUEPRINT → FILE TYPE ROUTER → 
FORMAT-SPECIFIC PROCESSOR → OCR + VISION → GEOMETRY EXTRACTION + SCALE CALIBRATION → 
ROOM / OBJECT DETECTION → BOQ + COST ESTIMATION → SUPABASE DATABASE → 
FRONTEND (Realtime) → DASHBOARD / VIEWER → OPTIONAL: USER CORRECTIONS
```

### Current Implementation Flow
```
USER → VITE + REACT FRONTEND → SUPABASE STORAGE → SUPABASE DATABASE → 
PYTHON WORKER (supabase_worker.py) → DOWNLOAD BLUEPRINT → FILE TYPE ROUTER → 
FORMAT-SPECIFIC PROCESSOR → OCR + VISION → GEOMETRY EXTRACTION + SCALE CALIBRATION → 
ROOM / OBJECT DETECTION → BOQ + COST ESTIMATION → SUPABASE DATABASE → 
FRONTEND (POLLING) → DASHBOARD / VIEWER → USER CORRECTIONS (partial)
```

**Status**: ✅ **ALIGNED** - Core flow matches, but missing Realtime subscriptions (currently uses polling)

---

## 2. Frontend Architecture Mapping

### ArchVision Requirements
- **Stack**: Vite + React + TypeScript ✅
- **Auth**: Clerk ✅
- **Responsibilities**: UI only, no heavy processing ✅
- **Realtime**: Supabase Realtime subscriptions ❌
- **Manual Calibration UI**: ✅ Implemented
- **Manual Correction UI**: ✅ Partially implemented
- **Supported Formats**: PDF, JPG/JPEG, DXF, IFC ✅

### Current Implementation
**File**: <ref_file file="/Users/swarajdeshmukh4249gmail.com/Desktop/blueprint-reader/frontend/package.json" />

**Status**: ✅ **MOSTLY ALIGNED**

**Implemented**:
- ✅ Vite + React + TypeScript stack
- ✅ Clerk authentication integration
- ✅ Project creation and blueprint upload
- ✅ Client-side file validation
- ✅ Upload to Supabase Storage
- ✅ Manual scale calibration UI (`ScaleCalibrationPage.tsx`)
- ✅ Manual correction UI (`CorrectionEditor.tsx`, `RoomEditor.tsx`)
- ✅ Dashboard, blueprint viewer, analytics
- ✅ Format support: PDF, JPG/JPEG, DXF, IFC

**Gaps**:
- ❌ **Supabase Realtime subscriptions** - Currently uses polling instead
- ❌ **Progress tracking via `current_stage`** - Not fully implemented
- ❌ **Retry button with `retry_of_job_id`** - Not implemented

**Key Files**:
- <ref_file file="/Users/swarajdeshmukh4249gmail.com/Desktop/blueprint-reader/frontend/src/App.tsx" />
- <ref_file file="/Users/swarajdeshmukh4249gmail.com/Desktop/blueprint-reader/frontend/src/pages/Upload.tsx" />
- <ref_file file="/Users/swarajdeshmukh4249gmail.com/Desktop/blueprint-reader/frontend/src/pages/Results.tsx" />
- <ref_file file="/Users/swarajdeshmukh4249gmail.com/Desktop/blueprint-reader/frontend/src/components/calibration/ScaleCalibration.tsx" />
- <ref_file file="/Users/swarajdeshmukh4249gmail.com/Desktop/blueprint-reader/frontend/src/components/correction/CorrectionEditor.tsx" />

---

## 3. Supabase Storage Mapping

### ArchVision Requirements
```
blueprints/
  {user_id}/
    {project_id}/
      original/
        blueprint.{ext}
      rendered/            ← temp page renders (PDF→image), TTL'd
```

### Current Implementation
**Status**: ⚠️ **PARTIALLY ALIGNED**

**Implemented**:
- ✅ Storage path structure exists
- ✅ Original file storage
- ✅ File type validation
- ✅ Integration with Supabase Storage

**Gaps**:
- ❌ **Rendered folder for PDF page images** - Not implemented
- ❌ **TTL/expiry for rendered images** - Not implemented
- ❌ **Signed URLs for frontend access** - May need verification

**Key Files**:
- <ref_file file="/Users/swarajdeshmukh4249gmail.com/Desktop/blueprint-reader/backend/services/storage.py" />

---

## 4. Supabase Database Schema Mapping

### ArchVision Required Tables

#### `projects`
**Spec**: `id, user_id, name, description, created_at, updated_at`

**Current**: <ref_file file="/Users/swarajdeshmukh4249gmail.com/Desktop/blueprint-reader/backend/migrations/001_initial_schema.sql" lines="48-66" />

**Status**: ✅ **ALIGNED** - Additional fields for organization support

#### `analysis_jobs`
**Spec**: `id, project_id, user_id, file_path, file_name, file_type, status, progress, current_stage, error_message, retry_of_job_id, created_at, started_at, completed_at`

**Current**: Uses `analysis_versions` table instead

**Status**: ❌ **MISMATCH** - Different table structure and naming

**Gaps**:
- ❌ Missing `analysis_jobs` table (uses `analysis_versions` instead)
- ❌ Missing `progress` field
- ❌ Missing `current_stage` field
- ❌ Missing `retry_of_job_id` field
- ❌ Status values differ (spec: `queued|processing|completed|failed`)

#### `rooms`
**Spec**: `id, project_id, job_id, name, type, length, width, height, area, confidence, geometry (jsonb), is_user_corrected (bool)`

**Current**: <ref_file file="/Users/swarajdeshmukh4249gmail.com/Desktop/blueprint-reader/backend/migrations/001_initial_schema.sql" lines="120-141" />

**Status**: ⚠️ **PARTIALLY ALIGNED**

**Implemented**:
- ✅ Basic room fields (name, type, area, dimensions, confidence)
- ✅ `polygon_coordinates` (jsonb) - similar to `geometry`
- ✅ Analysis version linkage (similar to job_id)

**Gaps**:
- ❌ **`is_user_corrected` field** - Missing
- ❌ **Normalized coordinates** - Current implementation may use raw pixels
- ❌ **Direct project linkage** - Currently linked through analysis_version

#### `dimensions`
**Spec**: `id, project_id, job_id, raw_text, value, unit, blueprint_coordinates (jsonb), linked_room_id, confidence, is_user_corrected`

**Status**: ❌ **MISSING** - No dedicated dimensions table

#### `detected_objects`
**Spec**: `id, project_id, job_id, object_type, geometry (jsonb), confidence`

**Status**: ❌ **MISSING** - No dedicated detected_objects table

#### `boq_items`
**Spec**: `id, project_id, job_id, material, category, quantity, unit, estimated_cost`

**Current**: <ref_file file="/Users/swarajdeshmukh4249gmail.com/Desktop/blueprint-reader/backend/migrations/001_initial_schema.sql" lines="191-206" />

**Status**: ✅ **ALIGNED** - Additional fields for rate cards and amounts

#### `analysis_results`
**Spec**: `id, project_id, job_id, total_floor_area, room_count, wall_length, door_count, window_count, estimated_material_cost, estimated_total_cost, confidence_score, scale_calibration (jsonb), processing_metadata (jsonb)`

**Status**: ⚠️ **PARTIALLY ALIGNED** - Data exists in `analysis_versions` but not as separate table

#### `corrections` (NEW)
**Spec**: `id, project_id, job_id, target_table, target_id, field, original_value, corrected_value, corrected_at, corrected_by_user_id`

**Status**: ❌ **MISSING** - No generic corrections table

**Current Correction Implementation**: <ref_file file="/Users/swarajdeshmukh4249gmail.com/Desktop/blueprint-reader/backend/api/correction.py" />

**Gaps**:
- ❌ No audit trail for corrections
- ❌ No generic correction logging system
- ❌ No `is_user_corrected` flags on entities

---

## 5. Python Backend / Worker Architecture

### ArchVision Required Structure
```
backend/
  main.py
  worker.py
  blueprint_logic.py       ← analyze_blueprint(file_path, file_type) router
  processors/
    pdf_processor.py
    image_processor.py
    dxf_processor.py
    ifc_processor.py
  vision/
    room_detection.py
    dimension_detection.py
    object_detection.py
  ocr/
    text_extraction.py
  calculations/
    scale.py
    area.py
    geometry.py
    quantity.py
    cost.py
  corrections/
    apply_correction.py
  database/
    supabase.py
```

### Current Implementation
**Status**: ⚠️ **PARTIALLY ALIGNED**

**Implemented**:
- ✅ `main.py` - FastAPI application <ref_file file="/Users/swarajdeshmukh4249gmail.com/Desktop/blueprint-reader/backend/main.py" />
- ✅ `supabase_worker.py` - Job processing worker <ref_file file="/Users/swarajdeshmukh4249gmail.com/Desktop/blueprint-reader/backend/supabase_worker.py" />
- ✅ `blueprint_logic.py` - Main analysis router <ref_file file="/Users/swarajdeshmukh4249gmail.com/Desktop/blueprint-reader/backend/blueprint_logic.py" />
- ✅ Format-specific processing in `blueprint_logic.py`
- ✅ Vision integration (`services/vision_analyzer.py`)
- ✅ OCR integration (in `blueprint_logic.py`)
- ✅ Scale calibration (`services/scale_calibrator.py`)
- ✅ BOQ calculation (`boq_engine.py`, `services/boq_calculator.py`)
- ✅ Correction service (`services/correction_service.py`)

**Gaps**:
- ❌ **Modular processor structure** - Logic is monolithic in `blueprint_logic.py`
- ❌ **Separate `processors/` directory** - Not organized as specified
- ❌ **Separate `vision/` directory** - Vision logic mixed in services
- ❌ **Separate `ocr/` directory** - OCR logic in main file
- ❌ **Separate `calculations/` directory** - Calculations in services
- ❌ **Separate `corrections/` directory** - Corrections in services
- ❌ **Separate `database/` directory** - DB logic in models

**Current Structure**:
```
backend/
  main.py ✅
  supabase_worker.py ✅ (similar to worker.py)
  blueprint_logic.py ✅
  boq_engine.py ✅
  pipelines/
    fusion.py
    geometry_ml.py
    ifc_parser.py ✅
    plan_engine.py
    scale_detection.py ✅
    wall_detection.py
  services/
    vision_analyzer.py ✅
    scale_calibrator.py ✅
    boq_calculator.py ✅
    correction_service.py ✅
    storage.py ✅
  models/ ✅ (database layer)
  api/ ✅ (API endpoints)
```

---

## 6. Format-Specific Processing Mapping

### ArchVision Requirements

#### PDF Processing
**Spec**: PyMuPDF → render pages to temp images → image pipeline

**Current**: <ref_file file="/Users/swarajdeshmukh4249gmail.com/Desktop/blueprint-reader/backend/blueprint_logic.py" lines="272-300" />

**Status**: ✅ **ALIGNED** - Uses PyMuPDF (fitz) for PDF processing

#### PNG/JPG Processing
**Spec**: OpenCV preprocessing → OCR → CV/vision model → geometry extraction

**Current**: Implemented in `blueprint_logic.py`

**Status**: ✅ **ALIGNED** - OpenCV, OCR, and vision pipeline present

#### DXF Processing
**Spec**: `ezdxf` → extract entities/layers → walls/lines/polylines/text/dimensions → geometry calculations → room detection

**Current**: Implemented in `blueprint_logic.py`

**Status**: ✅ **ALIGNED** - Uses ezdxf with native CAD geometry preference

#### IFC Processing
**Spec**: `ifcopenshell` → extract spatial structure → geometry + room detection from native BIM data

**Current**: <ref_file file="/Users/swarajdeshmukh4249gmail.com/Desktop/blueprint-reader/backend/pipelines/ifc_parser.py" />

**Status**: ✅ **ALIGNED** - Uses ifcopenshell for BIM data

#### DWG Processing
**Spec**: Explicitly OUT OF SCOPE for v1

**Current**: Not supported (as per spec)

**Status**: ✅ **ALIGNED** - Correctly excluded

---

## 7. Scale Calibration Mapping

### ArchVision Requirements
- Raster formats: detected dimension annotations → user-provided reference measurement
- DXF/IFC: native model units
- Never assume fixed scale
- Store in `scale_calibration jsonb`

### Current Implementation
**Status**: ✅ **ALIGNED**

**Implemented**:
- ✅ Scale detection for raster formats
- ✅ Manual calibration UI
- ✅ Native unit handling for DXF/IFC
- ✅ Scale calibration confidence scoring
- ✅ Scale calibration service

**Key Files**:
- <ref_file file="/Users/swarajdeshmukh4249gmail.com/Desktop/blueprint-reader/backend/services/scale_calibrator.py" />
- <ref_file file="/Users/swarajdeshmukh4249gmail.com/Desktop/blueprint-reader/backend/pipelines/scale_detection.py" />
- <ref_file file="/Users/swarajdeshmukh4249gmail.com/Desktop/blueprint-reader/frontend/src/components/calibration/ScaleCalibration.tsx" />

---

## 8. AI/Vision Layer Mapping

### ArchVision Requirements
- Use AI only for: room label recognition, symbol recognition, ambiguous object classification, verification
- Not for: deterministic geometry/CAD calculations
- OCR for text/dimension extraction
- Narrow, specific LLM/vision calls

### Current Implementation
**Status**: ✅ **ALIGNED**

**Implemented**:
- ✅ Vision model for ambiguous cases (Google Gemini)
- ✅ OCR for text/dimension extraction (Tesseract)
- ✅ Deterministic parsing preferred for CAD formats
- ✅ Fallback to vision when OCR fails

**Key Files**:
- <ref_file file="/Users/swarajdeshmukh4249gmail.com/Desktop/blueprint-reader/backend/services/vision_analyzer.py" />
- Vision integration in `blueprint_logic.py`

---

## 9. Pipeline Stage Weights Mapping

### ArchVision Spec
```
0%   queued
10%  preparing        (download + file-type identification)
25%  extracting        (format-specific parse)
45%  detecting         (OCR + object/room detection)
60%  calibrating       (scale calibration)
75%  calculating        (geometry: areas, wall lengths)
90%  estimating        (BOQ + cost)
100% finalizing → completed
```

### Current Implementation
**Status**: ❌ **NOT IMPLEMENTED**

**Gaps**:
- ❌ No `progress` field in jobs table
- ❌ No `current_stage` field in jobs table
- ❌ No stage-based progress updates
- ❌ Worker doesn't update progress during processing

---

## 10. Manual Correction Loop Mapping

### ArchVision Requirements
1. User views results, spots misdetected room/dimension
2. Frontend calls correction endpoint with `target_table`, `target_id`, `field`, `corrected_value`
3. Backend writes to `corrections`, updates target row, sets `is_user_corrected = true`
4. Backend recalculates dependent `analysis_results` aggregates
5. Frontend refreshes via Realtime or direct refetch

### Current Implementation
**Status**: ⚠️ **PARTIALLY ALIGNED**

**Implemented**:
- ✅ Manual correction UI
- ✅ Room update endpoint
- ✅ Room add/delete endpoints
- ✅ BOQ preview on correction

**Gaps**:
- ❌ **Generic `corrections` table** - Missing
- ❌ **`is_user_corrected` flags** - Missing
- ❌ **Correction audit trail** - Missing
- ❌ **Dependent aggregate recalculation** - Not implemented
- ❌ **Realtime refresh** - Uses polling instead

**Key Files**:
- <ref_file file="/Users/swarajdeshmukh4249gmail.com/Desktop/blueprint-reader/backend/api/correction.py" />
- <ref_file file="/Users/swarajdeshmukh4249gmail.com/Desktop/blueprint-reader/backend/services/correction_service.py" />

---

## 11. Error Handling & Retries Mapping

### ArchVision Requirements
- Catch and log full technical detail server-side
- Store only user-safe message in `error_message`
- Worker-side timeout/heartbeat to prevent orphaned jobs
- Retry = new `analysis_jobs` row with `retry_of_job_id`
- Never expose secrets in logs

### Current Implementation
**Status**: ⚠️ **PARTIALLY ALIGNED**

**Implemented**:
- ✅ Error handling in worker
- ✅ User-safe error messages
- ✅ Error logging

**Gaps**:
- ❌ **Worker heartbeat/timeout** - Not implemented
- ❌ **Retry with `retry_of_job_id`** - Not implemented
- ❌ **Orphaned job cleanup** - Not implemented

**Key Files**:
- <ref_file file="/Users/swarajdeshmukh4249gmail.com/Desktop/blueprint-reader/backend/supabase_worker.py" lines="203-218" />

---

## 12. Frontend Dashboard & Viewer Mapping

### ArchVision Requirements
- Project overview (floor area, room/door/window counts, wall length, cost)
- Room-by-room breakdown
- BOQ table
- Cost breakdown
- Split-pane blueprint viewer
- Click-to-highlight room ↔ drawing

### Current Implementation
**Status**: ✅ **ALIGNED**

**Implemented**:
- ✅ Dashboard with all metrics
- ✅ Room-by-room breakdown
- ✅ BOQ table
- ✅ Cost breakdown
- ✅ Blueprint viewer
- ⚠️ Click-to-highlight (may need verification with normalized coordinates)

**Key Files**:
- <ref_file file="/Users/swarajdeshmukh4249gmail.com/Desktop/blueprint-reader/frontend/src/pages/Dashboard.tsx" />
- <ref_file file="/Users/swarajdeshmukh4249gmail.com/Desktop/blueprint-reader/frontend/src/pages/Results.tsx" />
- <ref_file file="/Users/swarajdeshmukh4249gmail.com/Desktop/blueprint-reader/frontend/src/pages/Viewer.tsx" />

---

## 13. RLS under Clerk Mapping

### ArchVision Requirements
Two approaches:
1. **Service-role key in FastAPI**: FastAPI validates Clerk JWT, uses Supabase service-role key, enforces `user_id` scoping in app code
2. **Custom RLS via Clerk JWT**: Configure Supabase to accept Clerk JWTs, write RLS policies against Clerk's `sub` claim

### Current Implementation
**Status**: ⚠️ **PARTIALLY ALIGNED**

**Implemented**:
- ✅ Clerk JWT verification in FastAPI
- ✅ Service-role key usage in backend
- ✅ User-based scoping in API endpoints

**Gaps**:
- ❌ **RLS policies** - May not be properly configured for Clerk
- ❌ **Documented RLS approach decision** - Not specified

**Key Files**:
- <ref_file file="/Users/swarajdeshmukh4249gmail.com/Desktop/blueprint-reader/backend/auth/clerk.py" />

---

## 14. Separation of Concerns Mapping

### ArchVision Requirements
- **Vite/React** → UI and interaction only ✅
- **Supabase Storage** → original files ✅
- **Supabase DB** → metadata, jobs, structured results, corrections ✅
- **Python worker** → all heavy processing ✅
- **Vision/OCR** → interpretation, used narrowly ✅
- **Geometry engine** → measurements ✅
- **BOQ engine** → material quantities ✅
- **Cost engine** → pricing ✅

### Current Implementation
**Status**: ✅ **ALIGNED**

All separation of concerns are properly maintained in the current implementation.

---

## Gap Summary & Implementation Priorities

### Critical Gaps (Blocking ArchVision Compliance)

1. **❌ Database Schema Misalignment**
   - Missing `analysis_jobs` table (uses `analysis_versions`)
   - Missing `dimensions` table
   - Missing `detected_objects` table
   - Missing `corrections` table
   - Missing `is_user_corrected` flags
   - Missing `progress` and `current_stage` fields

2. **❌ Realtime Subscriptions**
   - Frontend uses polling instead of Supabase Realtime
   - Missing progress tracking via stage updates

3. **❌ Normalized Geometry Coordinates**
   - Need to verify if current geometry uses normalized (0-1) coordinates
   - Critical for click-to-highlight functionality

4. **❌ Retry Mechanism**
   - Missing `retry_of_job_id` field
   - No proper retry logic

### High Priority Gaps

5. **⚠️ Backend Code Organization**
   - Monolithic `blueprint_logic.py` needs modularization
   - Missing `processors/`, `vision/`, `ocr/`, `calculations/`, `corrections/` directories

6. **⚠️ Worker Reliability**
   - Missing heartbeat/timeout mechanism
   - No orphaned job cleanup

7. **⚠️ Correction Loop**
   - Missing generic corrections table
   - No dependent aggregate recalculation

### Medium Priority Gaps

8. **⚠️ Storage Structure**
   - Missing `rendered/` folder for PDF page images
   - No TTL/expiry for temporary files

9. **⚠️ RLS Configuration**
   - Need to document and verify RLS approach for Clerk

### Low Priority Gaps

10. **⚠️ Enhanced Error Handling**
    - Could improve error granularity
    - Better secret management

---

## Implementation Roadmap

### Phase 1: Database Schema Migration (Critical)
1. Create migration to add missing tables:
   - `analysis_jobs` (or rename `analysis_versions`)
   - `dimensions`
   - `detected_objects`
   - `corrections`
2. Add missing fields to existing tables:
   - `is_user_corrected` to `rooms`, `dimensions`
   - `progress`, `current_stage`, `retry_of_job_id` to jobs table
3. Migrate existing data to new schema
4. Update backend models to match new schema

### Phase 2: Realtime Implementation (Critical)
1. Replace frontend polling with Supabase Realtime subscriptions
2. Implement stage-based progress updates in worker
3. Add `current_stage` and `progress` field updates
4. Test Realtime fallback to polling

### Phase 3: Geometry Normalization (Critical)
1. Verify current coordinate system
2. Implement normalized coordinate conversion (0-1 range)
3. Update all geometry storage to use normalized coordinates
4. Test click-to-highlight functionality

### Phase 4: Retry Mechanism (High Priority)
1. Add `retry_of_job_id` field to jobs table
2. Implement retry logic in frontend
3. Update worker to handle retry jobs
4. Add retry UI with proper audit trail

### Phase 5: Backend Refactoring (High Priority)
1. Extract format-specific processors to `processors/` directory
2. Extract vision logic to `vision/` directory
3. Extract OCR logic to `ocr/` directory
4. Extract calculations to `calculations/` directory
5. Extract correction logic to `corrections/` directory
6. Update imports and test refactored code

### Phase 6: Correction Loop Enhancement (High Priority)
1. Implement generic `corrections` table
2. Add correction logging service
3. Implement dependent aggregate recalculation
4. Add `is_user_corrected` flags
5. Update correction UI to use new system

### Phase 7: Worker Reliability (Medium Priority)
1. Implement heartbeat mechanism
2. Add timeout handling
3. Implement orphaned job cleanup
4. Add monitoring and alerts

### Phase 8: Storage Enhancement (Medium Priority)
1. Add `rendered/` folder structure
2. Implement PDF page image rendering
3. Add TTL/expiry for temporary files
4. Implement cleanup automation

### Phase 9: RLS Configuration (Medium Priority)
1. Document RLS approach decision
2. Implement chosen RLS strategy
3. Test RLS policies thoroughly
4. Document RLS setup for future reference

---

## Conclusion

The current Blueprint Reader implementation is **well-architected and largely aligned** with the ArchVision v2 specification, with approximately **80% compliance**. The core functionality for blueprint analysis, format processing, scale calibration, and BOQ generation is solid and follows the specified separation of concerns.

The main gaps are in:
1. **Database schema structure** (critical)
2. **Realtime subscriptions** (critical)
3. **Geometry coordinate normalization** (critical)
4. **Code organization** (high priority)
5. **Correction loop audit trail** (high priority)

These gaps can be addressed through a phased implementation approach, with database schema and Realtime implementation being the highest priority for achieving full ArchVision compliance.