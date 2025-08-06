#!/bin/bash
# Reddit Claude Agent Service Launcher
# Manages the Reddit monitoring service with proper daemon behavior

set -e

# Configuration
SERVICE_NAME="Reddit Claude Agent"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_SCRIPT="$PROJECT_DIR/reddit_agent_service.py"
PID_FILE="$PROJECT_DIR/reddit_agent.pid"
LOG_FILE="$PROJECT_DIR/reddit_agent.log"
VENV_DIR="$PROJECT_DIR/venv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if service is running
is_running() {
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            # PID file exists but process is dead, clean up
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# Get service status
get_status() {
    if is_running; then
        local pid=$(cat "$PID_FILE")
        echo "running (PID: $pid)"
    else
        echo "stopped"
    fi
}

# Clean up any zombie processes
cleanup_processes() {
    log "Cleaning up any zombie processes..."
    
    # Find and kill any reddit_agent_service processes
    local pids=$(ps aux | grep "reddit_agent_service.py" | grep -v grep | awk '{print $2}')
    if [[ -n "$pids" ]]; then
        warning "Found zombie processes: $pids"
        echo "$pids" | xargs kill -TERM 2>/dev/null || true
        sleep 2
        # Force kill if still running
        echo "$pids" | xargs kill -KILL 2>/dev/null || true
    fi
    
    # Clear port 8080 if occupied
    local port_pid=$(lsof -ti:8080 2>/dev/null || true)
    if [[ -n "$port_pid" ]]; then
        warning "Port 8080 occupied by PID: $port_pid"
        kill -TERM "$port_pid" 2>/dev/null || true
        sleep 1
        kill -KILL "$port_pid" 2>/dev/null || true
    fi
    
    # Clean up stale PID file
    rm -f "$PID_FILE"
}

# Start the service
start_service() {
    log "Starting $SERVICE_NAME..."
    
    if is_running; then
        warning "Service is already running (PID: $(cat "$PID_FILE"))"
        return 0
    fi
    
    # Clean up any zombie processes first
    cleanup_processes
    
    # Check prerequisites
    if [[ ! -f "$SERVICE_SCRIPT" ]]; then
        error "Service script not found: $SERVICE_SCRIPT"
        return 1
    fi
    
    if [[ ! -f "$PROJECT_DIR/.env" ]]; then
        error "Environment file not found: $PROJECT_DIR/.env"
        error "Please copy .env.example to .env and configure Reddit API credentials"
        return 1
    fi
    
    # Activate virtual environment if it exists
    if [[ -d "$VENV_DIR" ]]; then
        source "$VENV_DIR/bin/activate"
        log "Activated virtual environment"
    else
        warning "Virtual environment not found, using system Python"
    fi
    
    # Start the service as a background daemon
    cd "$PROJECT_DIR"
    nohup python3 "$SERVICE_SCRIPT" > "$LOG_FILE" 2>&1 &
    local pid=$!
    
    # Save PID
    echo "$pid" > "$PID_FILE"
    
    # Wait a moment to check if it started successfully
    sleep 2
    
    if is_running; then
        success "$SERVICE_NAME started successfully (PID: $pid)"
        log "Logs: tail -f $LOG_FILE"
        
        # Show service status
        show_status
        
        # Offer to open monitor
        echo ""
        echo "Open service monitor? (y/n)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            open_monitor
        fi
    else
        error "Failed to start $SERVICE_NAME"
        error "Check logs: tail -f $LOG_FILE"
        return 1
    fi
}

# Stop the service
stop_service() {
    log "Stopping $SERVICE_NAME..."
    
    if ! is_running; then
        warning "Service is not running"
        return 0
    fi
    
    local pid=$(cat "$PID_FILE")
    
    # Send SIGTERM for graceful shutdown
    kill -TERM "$pid" 2>/dev/null || true
    
    # Wait for graceful shutdown
    local count=0
    while is_running && [[ $count -lt 10 ]]; do
        sleep 1
        ((count++))
    done
    
    # Force kill if still running
    if is_running; then
        warning "Forcing shutdown..."
        kill -KILL "$pid" 2>/dev/null || true
        sleep 1
    fi
    
    # Clean up PID file
    rm -f "$PID_FILE"
    
    success "$SERVICE_NAME stopped"
}

# Restart the service
restart_service() {
    log "Restarting $SERVICE_NAME..."
    stop_service
    sleep 2
    start_service
}

# Show service status
show_status() {
    local status=$(get_status)
    
    echo ""
    echo "============================================"
    echo "  $SERVICE_NAME Status"
    echo "============================================"
    echo "Status: $status"
    
    if is_running; then
        local pid=$(cat "$PID_FILE")
        echo "PID: $pid"
        echo "Memory: $(ps -o rss= -p "$pid" 2>/dev/null | awk '{print int($1/1024)" MB"}' || echo "Unknown")"
        echo "CPU: $(ps -o %cpu= -p "$pid" 2>/dev/null | awk '{print $1"%"}' || echo "Unknown")"
        
        # Show recent logs
        echo ""
        echo "Recent logs (last 5 lines):"
        echo "----------------------------"
        tail -n 5 "$LOG_FILE" 2>/dev/null || echo "No logs available"
    fi
    
    echo ""
    echo "Files:"
    echo "  Script: $SERVICE_SCRIPT"
    echo "  PID: $PID_FILE"
    echo "  Logs: $LOG_FILE"
    
    # Check health file if it exists
    local health_file="$PROJECT_DIR/service_health.json"
    if [[ -f "$health_file" ]]; then
        echo ""
        echo "Health Status:"
        echo "--------------"
        python3 -c "
import json
try:
    with open('$health_file', 'r') as f:
        health = json.load(f)
    print(f\"Status: {health.get('status', 'unknown')}\")
    print(f\"Uptime: {health.get('uptime_minutes', 0)} minutes\")
    print(f\"Total Insights: {health.get('total_insights', 0)}\")
    print(f\"Today\'s Insights: {health.get('insights_found_today', 0)}\")
    print(f\"Error Count: {health.get('error_count', 0)}\")
except Exception as e:
    print(f'Could not read health status: {e}')
" 2>/dev/null || echo "Could not read health status"
    fi
    
    echo "============================================"
}

# Open the web monitor
open_monitor() {
    local monitor_file="$PROJECT_DIR/reddit_agent_monitor.html"
    if [[ -f "$monitor_file" ]]; then
        log "Opening service monitor..."
        open "$monitor_file"
    else
        error "Monitor file not found: $monitor_file"
    fi
}

# Show logs
show_logs() {
    if [[ -f "$LOG_FILE" ]]; then
        log "Showing logs (press Ctrl+C to exit)..."
        tail -f "$LOG_FILE"
    else
        error "Log file not found: $LOG_FILE"
    fi
}

# Setup as macOS Launch Agent (optional)
setup_launch_agent() {
    local plist_file="$HOME/Library/LaunchAgents/com.ianswanson.reddit-claude-agent.plist"
    
    log "Setting up macOS Launch Agent..."
    
    cat > "$plist_file" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ianswanson.reddit-claude-agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>$0</string>
        <string>start</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$LOG_FILE</string>
    <key>StandardErrorPath</key>
    <string>$LOG_FILE</string>
</dict>
</plist>
EOF
    
    # Load the launch agent
    launchctl load "$plist_file" 2>/dev/null || true
    
    success "Launch Agent configured: $plist_file"
    log "Service will now start automatically on boot"
    log "To disable: launchctl unload $plist_file"
}

# Show help
show_help() {
    echo "Reddit Claude Agent Service Control"
    echo ""
    echo "Usage: $0 {start|stop|restart|status|logs|monitor|setup-auto|help}"
    echo ""
    echo "Commands:"
    echo "  start       Start the service"
    echo "  stop        Stop the service"
    echo "  restart     Restart the service"
    echo "  status      Show service status and health"
    echo "  logs        Show live logs (tail -f)"
    echo "  monitor     Open web-based monitor"
    echo "  setup-auto  Setup automatic startup on boot (macOS)"
    echo "  cleanup     Clean up zombie processes and free port"
    echo "  help        Show this help message"
}

# Main command handling
case "${1:-help}" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    monitor)
        open_monitor
        ;;
    setup-auto)
        setup_launch_agent
        ;;
    cleanup)
        cleanup_processes
        success "Cleanup completed"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
