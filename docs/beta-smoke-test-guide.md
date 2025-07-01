# Team Beta Smoke Test Guide (β-9)

## Current Status: IN PROGRESS

### Critical Checklist for Docker Smoke Test

1. **Environment Variables**
   ```bash
   # Ensure these are set in your .env file:
   OPENAI_API_KEY=<your-key>
   GOOGLE_API_KEY=<your-key>
   LANGFUSE_HOST=<your-host>
   LANGFUSE_PUBLIC_KEY=<your-key>
   LANGFUSE_SECRET_KEY=<your-key>
   GCS_BUCKET_NAME=reframe-apd-pdf
   GCS_PROJECT_ID=macayaven
   ```

2. **Build Docker Image**
   ```bash
   docker build -t reframe-orchestrator:latest .
   ```

3. **Run Container Locally**
   ```bash
   docker run -p 8000:8000 \
     --env-file .env \
     reframe-orchestrator:latest
   ```

4. **Test Endpoints**
   - Health check: `curl http://localhost:8000/health`
   - WebSocket: Connect to `ws://localhost:8000/chat/{session_id}`
   - Test conversation flow with the demo CLI

5. **Verify GCS Integration**
   - Ensure service account key is mounted/available
   - Test PDF upload to bucket
   - Verify public URL generation

### Common Issues & Fixes

**Issue**: Missing environment variables
- **Fix**: Double-check .env file and ensure all required vars are set

**Issue**: GCS authentication fails
- **Fix**: Verify service account key is correctly loaded from Secret Manager

**Issue**: WebSocket connection errors
- **Fix**: Check CORS settings and WebSocket route configuration

**Issue**: Container fails to start
- **Fix**: Check logs with `docker logs <container-id>`

### Next Steps After Smoke Test
1. Tag image for Artifact Registry: `docker tag reframe-orchestrator:latest gcr.io/macayaven/reframe-orchestrator:latest`
2. Push to registry (β-10)
3. Deploy to Cloud Run (β-11)

---
**Time is critical!** Integration phase starts at 13:35. If you encounter any blockers, report immediately!