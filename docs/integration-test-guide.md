# End-to-End Integration Test Guide

## 🎉 Congratulations! Here's how to test the complete system:

### 1. Local Testing (Development)

#### Option A: CLI Demo
```bash
cd /Users/carlos/workspace/retrame-agents-oai
uv run python -m app.assistants.demo_cli
```

This will start an interactive session where you can:
- Type messages in Spanish or English
- Test the intake flow: "Hola, me llamo Ana y tengo 28 años"
- Test crisis detection: "Tengo miedo de hablar con gente nueva"
- Accept PDF generation when offered

#### Option B: Direct API Testing
```bash
# Test the FastAPI backend
uv run python -m app.main

# In another terminal, test WebSocket connection
curl -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Version: 13" \
     -H "Sec-WebSocket-Key: SGVsbG8gV29ybGQ=" \
     http://localhost:8000/chat/test-session-123
```

### 2. Cloud Run Testing (Production)

If deployed to Cloud Run, test the live endpoint:

```bash
# Get the Cloud Run URL
gcloud run services describe reframe-edge --region europe-west1 --format 'value(status.url)'

# Test health endpoint
curl https://reframe-edge-[HASH]-ew.a.run.app/health

# Test WebSocket (use wscat or similar)
npm install -g wscat
wscat -c wss://reframe-edge-[HASH]-ew.a.run.app/chat/test-session-123
```

### 3. Full Conversation Test Script

Here's a complete test conversation:

```
User: "Hola"
Expected: Greeting and request for name, age, reason

User: "Me llamo Carlos, tengo 32 años y tengo mucho miedo de conocer gente nueva"
Expected: Context collected, moves to analysis phase