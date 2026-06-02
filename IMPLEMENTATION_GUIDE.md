# Enterprise Blueprint Analyzer - Implementation Guide

## Overview

This guide provides instructions for setting up and running the enterprise-grade Blueprint Analyzer SaaS platform.

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ with pgvector extension
- Clerk account (for authentication)
- AWS S3 or MinIO (for file storage)
- Clerk Secret Key and Publishable Key

## Setup Instructions

### 1. Database Setup

```bash
# Create PostgreSQL database
createdb blueprint_reader

# Enable pgvector extension
psql blueprint_reader
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

# Run migrations
cd backend
psql blueprint_reader < migrations/001_initial_schema.sql
psql blueprint_reader < migrations/002_audit_triggers.sql
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your values:
# DATABASE_URL=postgresql://user:password@localhost/blueprint_reader
# CLERK_SECRET_KEY=your_clerk_secret_key
# AWS_ACCESS_KEY_ID=your_aws_key
# AWS_SECRET_ACCESS_KEY=your_aws_secret
# S3_BUCKET_NAME=your_bucket_name

# Run the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set environment variables
cp .env.example .env
# Edit .env with your values:
# VITE_API_URL=http://localhost:8000/api/v1
# VITE_CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key

# Run the dev server
npm run dev
```

## Environment Variables

### Backend (.env)
```
DATABASE_URL=postgresql://user:password@localhost/blueprint_reader
CLERK_SECRET_KEY=sk_test_xxxxx
AWS_ACCESS_KEY_ID=AKIAxxxxx
AWS_SECRET_ACCESS_KEY=xxxxx
S3_BUCKET_NAME=blueprint-reader-files
USE_LOCAL_STORAGE=false
LOCAL_STORAGE_PATH=./storage
FRONTEND_ORIGIN=http://localhost:5173
```

### Frontend (.env)
```
VITE_API_URL=http://localhost:8000/api/v1
VITE_CLERK_PUBLISHABLE_KEY=pk_test_xxxxx
```

## API Endpoints

### Organizations
- `POST /api/v1/organizations` - Create organization
- `GET /api/v1/organizations` - List organizations
- `GET /api/v1/organizations/{id}` - Get organization
- `PUT /api/v1/organizations/{id}` - Update organization

### Projects
- `POST /api/v1/projects` - Create project
- `GET /api/v1/projects` - List projects
- `GET /api/v1/projects/{id}` - Get project
- `PUT /api/v1/projects/{id}` - Update project
- `DELETE /api/v1/projects/{id}` - Delete project

### Files
- `POST /api/v1/files/upload` - Upload file
- `GET /api/v1/files/{id}` - Get file
- `DELETE /api/v1/files/{id}` - Delete file

### Analysis
- `POST /api/v1/analysis/start` - Start analysis
- `GET /api/v1/analysis/{id}` - Get analysis
- `GET /api/v1/analysis/project/{project_id}` - List project analyses

### Diff
- `POST /api/v1/diff/compare/{v1_id}/{v2_id}` - Compare versions

### Correction
- `PUT /api/v1/correction/rooms/{id}` - Update room
- `POST /api/v1/correction/rooms` - Add room
- `DELETE /api/v1/correction/rooms/{id}` - Delete room
- `POST /api/v1/correction/analysis/{id}/boq-preview` - BOQ preview

### Calibration
- `POST /api/v1/calibration/analysis/{id}` - Calibrate scale

### Audit
- `GET /api/v1/audit/logs` - Get audit logs
- `GET /api/v1/audit/export/{org_id}` - Export audit logs

### Comments
- `POST /api/v1/comments` - Create comment
- `GET /api/v1/comments/project/{id}` - List comments
- `PUT /api/v1/comments/{id}` - Update comment
- `DELETE /api/v1/comments/{id}` - Delete comment

### Cost Engine
- `POST /api/v1/cost-engine/calculate` - Calculate cost
- `POST /api/v1/cost-engine/forecast` - Forecast cost
- `GET /api/v1/cost-engine/rate-trends/{material}` - Get rate trends

### Rate Cards
- `POST /api/v1/rate-cards` - Create rate card
- `GET /api/v1/rate-cards/organization/{id}` - List rate cards
- `POST /api/v1/rate-cards/items` - Add rate card item
- `GET /api/v1/rate-cards/{id}/items` - List rate card items

### Approvals
- `POST /api/v1/approvals/request` - Request approval
- `POST /api/v1/approvals/{id}/approve` - Approve
- `POST /api/v1/approvals/{id}/reject` - Reject
- `GET /api/v1/approvals/project/{id}` - List approvals
- `GET /api/v1/approvals/pending/{user_id}` - List pending approvals

## Features Implemented

### Phase 1 (Foundation)
- ✅ Multi-tenant PostgreSQL database schema
- ✅ Clerk authentication with RBAC
- ✅ Organization and project management APIs
- ✅ File upload system with S3/MinIO
- ✅ Blueprint analysis integration
- ✅ React dashboard with project list

### Phase 2 (Core Features)
- ✅ Analysis version control system
- ✅ Visual diff component for version comparison
- ✅ Manual correction tool with Konva canvas
- ✅ Real-time BOQ preview on room changes
- ✅ Scale calibration UI and backend service
- ✅ PDF/Excel export services with branding
- ✅ Audit trail with database triggers
- ✅ Comment system for collaboration

### Phase 3 (Advanced Features)
- ✅ Region-based cost engine service
- ✅ Rate card management system
- ✅ Three.js CAD viewer for DXF files
- ✅ IFC viewer with Three.js
- ✅ Enterprise analytics dashboard
- ✅ Approval workflow system

## Next Steps

1. **Install Dependencies**: Run `npm install` in frontend and `pip install -r requirements.txt` in backend
2. **Configure Environment**: Set up Clerk keys and database connection
3. **Run Migrations**: Execute SQL migration files
4. **Start Services**: Run backend and frontend servers
5. **Test Features**: Navigate to http://localhost:5173 to test the application

## Notes

- The `react-konva` package needs to be installed for the correction and diff tools
- Three.js is used for CAD/BIM file preview
- Recharts is used for the analytics dashboard
- All API routes are prefixed with `/api/v1`
- Clerk authentication is required for accessing protected routes
