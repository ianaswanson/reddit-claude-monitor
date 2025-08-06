#!/usr/bin/env python3
"""
Reddit Claude Intelligence Monitor - AI Agent Service with API
Always-on background service with web API for real dashboard connectivity
"""

import os
import sys
import time
import json
import signal
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import praw
import schedule
from dotenv import load_dotenv

# Service status tracking
class ServiceStatus(Enum):
    STARTING = "starting"
    RUNNING = "running"
    HEALTHY = "healthy"
    ERROR = "error"
    STOPPING = "stopping"
    STOPPED = "stopped"

@dataclass
class ServiceHealth:
    status: ServiceStatus
    last_check: datetime
    last_success: Optional[datetime]
    error_count: int
    uptime_start: datetime
    insights_found_today: int
    total_insights: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'status': self.status.value,
            'last_check': self.last_check.isoformat(),
            'last_success': self.last_success.isoformat() if self.last_success else None,
            'error_count': self.error_count,
            'uptime_start': self.uptime_start.isoformat(),
            'uptime_minutes': int((datetime.now() - self.uptime_start).total_seconds() / 60),
            'insights_found_today': self.insights_found_today,
            'total_insights': self.total_insights
        }

class APIHandler(BaseHTTPRequestHandler):
    """HTTP API handler for service status and insights"""
    
    def __init__(self, service_instance, *args, **kwargs):
        self.service = service_instance
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        try:
            if path == '/health' or path == '/api/health':
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                health_data = self.service.health_check()
                self.wfile.write(json.dumps(health_data).encode())
                
            elif path == '/insights' or path == '/api/insights':
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                insights_data = self.service.get_recent_insights()
                self.wfile.write(json.dumps(insights_data).encode())
                
            elif path == '/api/insights/recent':
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                # Get query parameters
                query_params = parse_qs(parsed_path.query)
                limit = int(query_params.get('limit', [10])[0])
                
                recent_insights = self.service.get_recent_insights(limit=limit)
                self.wfile.write(json.dumps(recent_insights).encode())
                
            else:
                self.send_response(404)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Endpoint not found'}).encode())
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress default HTTP request logging"""
        pass

class RedditAgentService:
    """AI Agent Service for Reddit Claude Intelligence Monitoring"""
    
    def __init__(self):
        # Load environment
        load_dotenv()
        
        # Service configuration
        self.service_name = "Reddit Claude Intelligence Monitor"
        self.check_interval = int(os.getenv('CHECK_INTERVAL_HOURS', '1'))  # Check every hour
        self.api_port = int(os.getenv('API_PORT', '8080'))
        self.data_dir = Path(__file__).parent
        self.health_file = self.data_dir / 'service_health.json'
        self.insights_file = self.data_dir / 'claude_insights.json'
        
        # Service state
        self.running = False
        self.health = ServiceHealth(
            status=ServiceStatus.STARTING,
            last_check=datetime.now(),
            last_success=None,
            error_count=0,
            uptime_start=datetime.now(),
            insights_found_today=0,
            total_insights=0
        )
        
        # API server
        self.api_server = None
        self.api_thread = None
        
        # Monitoring
        self.setup_logging()
        self.load_health_state()
        
        # Reddit API setup
        self.setup_reddit_api()
        
        # Graceful shutdown handling
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def setup_logging(self):
        """Configure structured logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.data_dir / 'reddit_agent.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('RedditAgent')
        
    def setup_reddit_api(self):
        """Initialize Reddit API connection"""
        try:
            self.reddit = praw.Reddit(
                client_id=os.getenv('REDDIT_CLIENT_ID'),
                client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
                user_agent=os.getenv('REDDIT_USER_AGENT', 'ClaudeIntelligenceMonitor/2.0-Service')
            )
            self.subreddit_name = os.getenv('SUBREDDIT', 'claude')
            self.min_relevance_score = float(os.getenv('MIN_RELEVANCE_SCORE', '0.7'))
            self.logger.info("Reddit API initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Reddit API: {e}")
            self.health.status = ServiceStatus.ERROR
            raise
    
    def start_api_server(self):
        """Start the HTTP API server in a separate thread"""
        try:
            def create_handler(*args, **kwargs):
                return APIHandler(self, *args, **kwargs)
            
            self.api_server = HTTPServer(('localhost', self.api_port), create_handler)
            self.api_thread = threading.Thread(target=self.api_server.serve_forever, daemon=True)
            self.api_thread.start()
            
            self.logger.info(f"API server started on http://localhost:{self.api_port}")
            self.logger.info(f"Health endpoint: http://localhost:{self.api_port}/health")
            self.logger.info(f"Insights endpoint: http://localhost:{self.api_port}/insights")
            
        except Exception as e:
            self.logger.error(f"Failed to start API server: {e}")
    
    def stop_api_server(self):
        """Stop the HTTP API server"""
        if self.api_server:
            self.api_server.shutdown()
            self.api_server.server_close()
            if self.api_thread:
                self.api_thread.join(timeout=5)
            self.logger.info("API server stopped")
    
    def load_health_state(self):
        """Load previous health state if available"""
        try:
            if self.health_file.exists():
                with open(self.health_file, 'r') as f:
                    data = json.load(f)
                    # Restore some persistent metrics
                    self.health.total_insights = data.get('total_insights', 0)
                    self.logger.info(f"Loaded health state: {self.health.total_insights} total insights")
        except Exception as e:
            self.logger.warning(f"Could not load previous health state: {e}")
    
    def save_health_state(self):
        """Persist health state to disk"""
        try:
            with open(self.health_file, 'w') as f:
                json.dump(self.health.to_dict(), f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save health state: {e}")
    
    def update_status(self, status: ServiceStatus, error: Optional[str] = None):
        """Update service status with logging and persistence"""
        old_status = self.health.status
        self.health.status = status
        self.health.last_check = datetime.now()
        
        if status == ServiceStatus.ERROR:
            self.health.error_count += 1
            self.logger.error(f"Service error: {error}")
        elif status == ServiceStatus.HEALTHY:
            self.health.last_success = datetime.now()
            if old_status == ServiceStatus.ERROR:
                self.logger.info("Service recovered from error state")
        
        self.logger.info(f"Status changed: {old_status.value} → {status.value}")
        self.save_health_state()
    
    def calculate_relevance_score(self, post) -> float:
        """Calculate relevance score for a post (0.0 to 1.0)"""
        score = 0.0
        
        # Keywords that indicate valuable content
        valuable_keywords = [
            'tip', 'trick', 'technique', 'prompt', 'workflow', 'automation',
            'api', 'integration', 'coding', 'development', 'productivity',
            'best practice', 'lesson learned', 'tutorial', 'guide', 'method'
        ]
        
        # Check title and text for valuable keywords
        title = post.title.lower()
        text = getattr(post, 'selftext', '').lower()
        content = f"{title} {text}"
        
        # Keyword scoring
        keyword_matches = sum(1 for keyword in valuable_keywords if keyword in content)
        score += min(keyword_matches * 0.1, 0.5)  # Up to 0.5 for keywords
        
        # Engagement scoring
        upvote_ratio = getattr(post, 'upvote_ratio', 0)
        score += upvote_ratio * 0.3  # Up to 0.3 for upvote ratio
        
        # Comment engagement
        num_comments = getattr(post, 'num_comments', 0)
        if num_comments > 5:
            score += 0.2  # Boost for discussion
        
        return min(score, 1.0)  # Cap at 1.0
    
    def extract_insight(self, post) -> Dict[str, Any]:
        """Extract structured insight from a post"""
        return {
            'id': post.id,
            'title': post.title,
            'author': str(post.author) if post.author else '[deleted]',
            'url': f"https://reddit.com{post.permalink}",
            'score': post.score,
            'num_comments': post.num_comments,
            'created_utc': post.created_utc,
            'text': getattr(post, 'selftext', '')[:500],  # First 500 chars
            'relevance_score': self.calculate_relevance_score(post),
            'discovered_date': datetime.now().isoformat()
        }
    
    def check_for_insights(self) -> int:
        """Main monitoring logic - check for new valuable posts"""
        try:
            self.logger.info("Starting Reddit monitoring check...")
            subreddit = self.reddit.subreddit(self.subreddit_name)
            
            # Load processed posts to avoid duplicates
            processed_posts = set()
            insights_data = {'insights': [], 'processed_ids': []}
            
            if self.insights_file.exists():
                with open(self.insights_file, 'r') as f:
                    insights_data = json.load(f)
                    processed_posts = set(insights_data.get('processed_ids', []))
            
            new_insights = []
            posts_checked = 0
            
            # Check recent posts
            for post in subreddit.hot(limit=50):
                posts_checked += 1
                
                # Skip if already processed
                if post.id in processed_posts:
                    continue
                
                # Calculate relevance
                relevance = self.calculate_relevance_score(post)
                
                # Only include if meets minimum relevance threshold
                if relevance >= self.min_relevance_score:
                    insight = self.extract_insight(post)
                    new_insights.append(insight)
                    self.logger.info(f"Found valuable post: {post.title[:50]}... (score: {relevance:.2f})")
                
                # Mark as processed
                processed_posts.add(post.id)
            
            # Save updated insights
            if new_insights:
                insights_data['insights'].extend(new_insights)
                insights_data['processed_ids'] = list(processed_posts)
                insights_data['last_updated'] = datetime.now().isoformat()
                
                with open(self.insights_file, 'w') as f:
                    json.dump(insights_data, f, indent=2)
                
                # Update metrics
                self.health.insights_found_today += len(new_insights)
                self.health.total_insights += len(new_insights)
                
                # Send notification
                self.send_notification(new_insights)
            
            self.logger.info(f"Check complete: {posts_checked} posts checked, {len(new_insights)} new insights found")
            self.update_status(ServiceStatus.HEALTHY)
            
            return len(new_insights)
            
        except Exception as e:
            self.logger.error(f"Error during monitoring check: {e}")
            self.update_status(ServiceStatus.ERROR, str(e))
            return 0
    
    def send_notification(self, insights):
        """Send desktop notification for new insights"""
        try:
            # macOS notification
            title = f"Reddit Claude Monitor - {len(insights)} New Insights!"
            message = f"Found {len(insights)} valuable posts in r/{self.subreddit_name}"
            
            os.system(f'osascript -e \'display notification "{message}" with title "{title}"\'')
            
            # Also create a daily digest file
            self.create_daily_digest(insights)
            
        except Exception as e:
            self.logger.error(f"Failed to send notification: {e}")
    
    def create_daily_digest(self, insights):
        """Create human-readable daily digest"""
        try:
            summary = f"\n🔍 CLAUDE INTELLIGENCE DIGEST - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            summary += f"Found {len(insights)} valuable posts:\n\n"
            
            # Sort by relevance score
            insights.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            for i, insight in enumerate(insights, 1):
                summary += f"{i}. {insight['title']}\n"
                summary += f"   👤 u/{insight['author']} | ⬆️ {insight['score']} | 💬 {insight['num_comments']}\n"
                summary += f"   🔗 {insight['url']}\n"
                if insight['text']:
                    summary += f"   📝 {insight['text'][:100]}...\n"
                summary += f"   📊 Relevance: {insight['relevance_score']:.2f}\n\n"
            
            # Save digest
            digest_file = self.data_dir / f"claude_digest_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
            with open(digest_file, 'w') as f:
                f.write(summary)
                
        except Exception as e:
            self.logger.error(f"Failed to create daily digest: {e}")
    
    def get_recent_insights(self, limit: int = 10) -> Dict[str, Any]:
        """Get recent insights for API consumption"""
        try:
            if not self.insights_file.exists():
                return {'insights': [], 'total_count': 0}
            
            with open(self.insights_file, 'r') as f:
                data = json.load(f)
                insights = data.get('insights', [])
                
                # Sort by discovery date (most recent first)
                insights.sort(key=lambda x: x.get('discovered_date', ''), reverse=True)
                
                # Return limited set
                return {
                    'insights': insights[:limit],
                    'total_count': len(insights),
                    'last_updated': data.get('last_updated')
                }
                
        except Exception as e:
            self.logger.error(f"Error getting recent insights: {e}")
            return {'insights': [], 'total_count': 0, 'error': str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Return current service health status"""
        # Reset daily counter if new day
        if self.health.last_check.date() < datetime.now().date():
            self.health.insights_found_today = 0
        
        health_data = self.health.to_dict()
        health_data['api_port'] = self.api_port
        return health_data
    
    def run_service(self):
        """Main service loop"""
        self.logger.info(f"Starting {self.service_name} service...")
        self.running = True
        self.update_status(ServiceStatus.RUNNING)
        
        # Start API server
        self.start_api_server()
        
        # Schedule monitoring checks
        schedule.every(self.check_interval).hours.do(self.check_for_insights)
        
        # Run initial check
        self.logger.info("Running initial monitoring check...")
        self.check_for_insights()
        
        # Main service loop
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(30)  # Check every 30 seconds
                
        except Exception as e:
            self.logger.error(f"Service loop error: {e}")
            self.update_status(ServiceStatus.ERROR, str(e))
        
        # Cleanup
        self.stop_api_server()
        self.logger.info("Service stopped")
        self.update_status(ServiceStatus.STOPPED)
    
    def signal_handler(self, signum, frame):
        """Handle graceful shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.update_status(ServiceStatus.STOPPING)
        self.running = False
    
    def stop_service(self):
        """Stop the service"""
        self.running = False

def main():
    """Main entry point"""
    # Load environment variables first
    load_dotenv()
    
    if not os.getenv('REDDIT_CLIENT_ID'):
        print("❌ Reddit API credentials not configured!")
        print("1. Copy .env.example to .env")
        print("2. Get Reddit API credentials from https://www.reddit.com/prefs/apps")
        print("3. Fill in your credentials in .env file")
        return
    
    service = RedditAgentService()
    
    try:
        service.run_service()
    except KeyboardInterrupt:
        print("\n👋 Service stopped by user")
    except Exception as e:
        print(f"❌ Service failed: {e}")
        service.logger.error(f"Service failed: {e}")

if __name__ == "__main__":
    main()
