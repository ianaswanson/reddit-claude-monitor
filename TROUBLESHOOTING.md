# Reddit Claude Monitor - Troubleshooting Guide

## Recurring Issues & Solutions

### Issue #1: Service Shows "Error" Status on Dashboard

**Symptoms:**
- Dashboard displays service in "error" state
- `service_health.json` shows `"status": "error"`
- 401 HTTP response errors in logs

**Root Causes Identified:**
1. **Multiple service instances running simultaneously**
   - Previous service instances not properly terminated
   - PID file exists but points to dead process
   - New instances fail to bind to port 8080

2. **Port conflicts (Address already in use)**
   - Port 8080 occupied by zombie processes
   - Multiple Python processes running the service

**Diagnostic Commands:**
```bash
# Check service processes
ps aux | grep -E "reddit_(agent_service|monitor)" | grep -v grep

# Check port usage
lsof -i :8080

# Check service health
cat service_health.json

# Check recent logs
tail -20 reddit_agent.log
```

**Resolution Steps:**
1. **Kill all service processes:**
   ```bash
   # Find PIDs
   ps aux | grep reddit_agent_service | grep -v grep | awk '{print $2}' | xargs kill
   
   # Or kill specific processes
   kill [PID1] [PID2] [PID3]
   ```

2. **Clear port 8080:**
   ```bash
   # Find what's using port 8080
   lsof -i :8080
   
   # Kill the process
   kill [PID]
   ```

3. **Clean restart using control script:**
   ```bash
   ./service_control.sh stop
   ./service_control.sh start
   ```

**Prevention:**
- Always use `./service_control.sh` instead of direct Python execution
- Ensure proper shutdown before starting new instances
- Monitor for zombie processes

### Issue #2: Reddit API Authentication Failures

**Symptoms:**
- "received 401 HTTP response" errors
- Service starts but immediately goes to error state
- No insights being collected

**Root Causes:**
- Reddit API credentials invalid/expired
- Environment variables not loaded properly
- Missing `.env` file

**Diagnostic Commands:**
```bash
# Check environment variables
echo "REDDIT_CLIENT_ID=${REDDIT_CLIENT_ID:-not set}"

# Verify .env file exists and has content
cat .env

# Test authentication manually
python -c "
from dotenv import load_dotenv
import os, praw
load_dotenv()
reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    user_agent=os.getenv('REDDIT_USER_AGENT')
)
print('Auth test:', reddit.subreddit('claude').display_name)
"
```

**Resolution:**
1. Verify Reddit app credentials at https://www.reddit.com/prefs/apps
2. Update `.env` file with valid credentials
3. Restart service

## Service Management Best Practices

### Always Use Control Script
```bash
# ✅ Correct
./service_control.sh start
./service_control.sh stop
./service_control.sh restart
./service_control.sh status

# ❌ Avoid direct execution
python reddit_agent_service.py
nohup python reddit_agent_service.py &
```

### Before Starting Service
1. Check no existing processes: `ps aux | grep reddit_agent`
2. Verify port availability: `lsof -i :8080`
3. Confirm `.env` file exists and is valid

### Monitoring Commands
```bash
# Service status and health
./service_control.sh status

# Live logs
./service_control.sh logs

# Quick health check
curl -s http://localhost:8080/health | python -m json.tool
```

## Common Error Patterns

### "Address already in use" (Port 8080)
- **Cause:** Previous instance still running or zombie process
- **Fix:** Kill processes using port 8080, then restart

### "Status changed: running → error"
- **Cause:** Usually Reddit API authentication failure
- **Fix:** Verify API credentials and network connectivity

### Service starts but no API server
- **Cause:** Port conflict prevents API server startup
- **Fix:** Clear port, restart service

## Emergency Recovery
```bash
# Nuclear option: kill everything and restart
pkill -f reddit_agent
rm -f reddit_agent.pid
lsof -ti:8080 | xargs kill -9 2>/dev/null || true
./service_control.sh start
```

## File Locations
- Service script: `reddit_agent_service.py`
- Control script: `service_control.sh`
- Health status: `service_health.json`
- Logs: `reddit_agent.log`
- PID file: `reddit_agent.pid`
- Configuration: `.env`

---
*Last updated: 2025-08-06*
*Issue frequency: Weekly (process management problems)*