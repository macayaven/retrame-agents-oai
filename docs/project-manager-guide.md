# Project Manager Guide - Reframe-APD MVP Sprint

## Your Role
As Project Manager, you oversee the 3-hour MVP sprint, coordinate between teams, resolve blockers, and ensure quality delivery. You have final approval on all PRs.

## Sprint Timeline: 11:05 - 14:00

### Key Milestones
- **11:05**: Sprint begins, teams start parallel work
- **12:15**: CRITICAL HANDSHAKE - Team β shares GCS credentials with Team α
- **13:35**: Integration phase begins
- **14:00**: PR submitted, MVP complete

## Project Tracking

### GitHub Projects
- **Project 5**: Backend tasks (Team α) - https://github.com/users/macayaven/projects/5
- **Project 4**: Frontend/Infra tasks (Team β) - https://github.com/users/macayaven/projects/4

### Team Assignments
- **Team α**: Backend/AI Engineer working in `retrame-agents-oai`
- **Team β**: DevOps/Frontend Engineer working in `re-frame` and infrastructure

## Critical Coordination Points

### 12:15 - GCS Handshake
**Your Actions:**
1. Verify Team β has completed β-3 (service account creation)
2. Ensure they comment on issue α-11 with:
   - Bucket name: `reframe-apd-pdf`
   - Service account email
   - Project ID
3. Confirm Team α acknowledges receipt
4. Monitor α-11 and α-12 progress

### 13:35 - Integration Phase
**Your Actions:**
1. Verify all individual tasks are complete
2. Coordinate joint testing:
   - Backend WebSocket endpoint live
   - Frontend connects successfully
   - PDF flow works end-to-end
3. Review code quality checks
4. Prepare for PR creation

## Quality Gates Checklist

### Backend (Team α)
- [ ] All 13 tasks completed
- [ ] 25 tests passing
- [ ] Coverage ≥70%
- [ ] `poe check` passes (ruff, black, mypy)
- [ ] No hardcoded secrets

### Frontend/Infra (Team β)  
- [ ] All 15 tasks completed
- [ ] Docker image < 220MB
- [ ] Cloud Run deployed successfully
- [ ] Cold start < 5s
- [ ] Frontend builds without errors

### Integration
- [ ] WebSocket connection established
- [ ] State transitions work correctly
- [ ] PDF generation and download functional
- [ ] Crisis path tested
- [ ] Spanish/English support verified

## Communication Protocols

### Slack/Discord Channels
- `#mvp-sprint` - General coordination
- `#team-alpha` - Backend discussions
- `#team-beta` - Frontend/DevOps discussions
- `#blockers` - Urgent issues

### Issue Management
- Teams update issue status in real-time
- Blockers tagged with `blocker` label
- Dependencies marked with `dependency` label
- Critical path items have `critical-path` label

## Blocker Resolution Process

1. **Identify**: Team member comments on issue with `@pm-help`
2. **Assess**: Determine impact on critical path
3. **Resolve**: 
   - Technical blockers: Provide guidance or reassign
   - Dependency blockers: Expedite handoffs
   - Resource blockers: Reallocate tasks
4. **Track**: Update issue with resolution

## PR Review Process

### 13:45 - Pre-Review
1. Both teams push final commits
2. Run CI/CD checks
3. Verify all DoD criteria met

### 14:00 - Final PR
**Title**: `feat: orchestrator MVP (backend+infra+FE)`

**PR Description Template**:
```markdown
## Summary
Implements MVP orchestrator with WebSocket streaming, GCS integration, and frontend UI updates.

## Changes
### Backend (Team α)
- State machine implementation
- OpenAI orchestrator assistant
- Tool implementations with offline stubs
- 25 unit tests with 70%+ coverage

### Infrastructure & Frontend (Team β)
- GCS bucket and service account setup
- Cloud Run deployment
- WebSocket integration
- PDF download UI component

## Testing
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] Manual E2E test completed
- [ ] Crisis detection verified

## Deployment
- Cloud Run URL: [URL]
- Environment: Staging
```

## Emergency Procedures

### If Team Falls Behind
1. Identify non-critical tasks that can be deferred
2. Reassign tasks between teams if one finishes early
3. Focus on critical path items only

### If Critical Dependency Blocked
1. Implement temporary workaround
2. Document technical debt
3. Create follow-up issue for proper implementation

### If Quality Gates Fail
1. Assess if issue is blocking
2. Create hotfix branch if needed
3. Document known issues in PR

## Success Metrics
- [ ] MVP deployed and accessible
- [ ] Core flow works: intake → analysis → PDF
- [ ] Crisis detection functional
- [ ] Both teams finish within 3-hour window
- [ ] Clean PR ready for review

## Post-Sprint Actions
1. Merge PR after approval
2. Deploy to staging environment
3. Schedule demo with stakeholders
4. Create issues for technical debt
5. Plan next sprint based on learnings

---

Remember: Your primary role is to keep teams unblocked and ensure smooth coordination. Be proactive in identifying potential issues and facilitating communication between teams.