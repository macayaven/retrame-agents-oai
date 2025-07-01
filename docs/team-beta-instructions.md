# Team β (DevOps/Frontend) Instructions

## Mission
You are the DevOps/Frontend Engineer responsible for infrastructure setup, Cloud Run deployment, and frontend WebSocket integration for the Reframe-APD MVP. Your work spans GCS setup, Docker, Cloud Run, and React/Next.js updates.

## Timeline: 3-Hour Sprint (11:05 - 14:00)

### Your Tasks
All tasks are tracked as GitHub issues in [Project 4](https://github.com/users/macayaven/projects/4). Work through them in order:

1. **β-1** (2m): Pull latest code & create feature branch
2. **β-2** (5m): Create GCS bucket `reframe-apd-pdf` in eu-west1
3. **β-3** (5m): Create service account & permissions **[CRITICAL - Share with Team α at 12:15]**
4. **β-4** (3m): Store SA key in Secret Manager
5. **β-5** (4m): Add environment variables to settings
6. **β-6** (15m): Add WebSocket route to FastAPI backend
7. **β-7** (10m): Replace Supabase with GCS in PDF service
8. **β-8** (10m): Build multi-stage Docker image
9. **β-9** (3m): Local container smoke test
10. **β-10** (7m): Push to Artifact Registry
11. **β-11** (8m): Deploy to Cloud Run
12. **β-12** (4m): Update frontend API URL
13. **β-13** (12m): Update socket.ts event handling
14. **β-14** (10m): Create PDF download component
15. **β-15** (3m): Add PR template & CI badge

### Critical Handshake Point
**At 12:15**: After completing β-3, immediately share with Team α:
- Comment on their issue α-11 with:
  - Bucket name: `reframe-apd-pdf`
  - Service account email: `reframe-edge-sa@PROJECT_ID.iam.gserviceaccount.com`
  - Project ID: `[your-project-id]`

### Technical Specifications

#### GCS Setup (β-2, β-3)
```bash
# Create bucket
gsutil mb -p PROJECT_ID -c STANDARD -l EU-WEST1 gs://reframe-apd-pdf/

# Create service account
gcloud iam service-accounts create reframe-edge-sa \
  --display-name="Reframe Edge Service Account"

# Grant permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:reframe-edge-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectCreator"
```

#### WebSocket Route (β-6)
Add to `backend/app/main.py`:
```python
@app.websocket("/chat/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    # Implementation details...
```

#### Frontend Socket Events (β-13)
Update `lib/socket.ts` to handle:
- `init` → Backend
- `user_msg` → Backend  
- `assistant_stream` ← Backend
- `phase_change` ← Backend
- `pdf_ready` ← Backend
- `complete` ← Backend

#### Docker Requirements (β-8)
- Multi-stage build
- Distroless final image
- Target size < 220MB
- Include all Python dependencies

#### Cloud Run Deploy (β-11)
```bash
gcloud run deploy reframe-edge \
  --source . \
  --service-account reframe-edge-sa@PROJECT_ID.iam.gserviceaccount.com \
  --region eu-west1 \
  --allow-unauthenticated
```

### Environment Setup
```bash
# Work in both directories as needed
cd /Users/carlos/workspace/re-frame  # For frontend tasks
cd /Users/carlos/workspace/retrame-agents-oai  # For backend tasks

# Ensure gcloud is configured
gcloud auth login
gcloud config set project PROJECT_ID
```

### Quality Standards
- Frontend: ESLint clean, TypeScript no errors
- Backend: Container < 220MB
- Cloud Run: Cold start < 5s
- All environment variables properly configured
- No hardcoded secrets

### Communication
- Update issue status as you progress
- **CRITICAL**: Share GCS details at 12:15 sharp
- Coordinate with Team α for final integration at 13:35
- Test end-to-end flow before PR

### Definition of Done
- All 15 tasks completed
- Cloud Run endpoint accessible
- Frontend connects via WebSocket
- PDF download works (dummy in OFFLINE mode)
- CI/CD pipeline configured
- Ready to merge into PR by 14:00

## Quick Reference

### Frontend Working Directory
```
/Users/carlos/workspace/re-frame
```

### Backend Working Directory  
```
/Users/carlos/workspace/retrame-agents-oai
```

### Key Files to Modify
- `backend/app/main.py` - WebSocket route
- `frontend/lib/socket.ts` - Event handling
- `frontend/components/PdfChip.tsx` - New component
- `backend/Dockerfile` - Multi-stage build
- `.env.example` - Environment variables

## Questions?
Contact the Project Manager immediately if you encounter any blockers or need clarification.

Good luck! 🚀