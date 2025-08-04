#!/usr/bin/env python3
"""
Reddit Claude Intelligence Monitor
Automated monitoring of r/claude for valuable insights and techniques
"""

import praw
import json
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dotenv import load_dotenv

class RedditClaudeMonitor:
    def __init__(self):
        """Initialize the Reddit monitor with API credentials"""
        load_dotenv()
        
        # Reddit API setup
        self.reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USER_AGENT', 'ClaudeIntelligenceMonitor/1.0')
        )
        
        # Configuration
        self.subreddit_name = os.getenv('SUBREDDIT', 'claude')
        self.min_relevance_score = float(os.getenv('MIN_RELEVANCE_SCORE', '0.7'))
        
        # Data storage
        self.data_file = 'claude_insights.json'
        self.processed_posts = self.load_processed_posts()
        
    def load_processed_posts(self) -> set:
        """Load previously processed post IDs to avoid duplicates"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('processed_ids', []))
        except Exception as e:
            print(f"Error loading processed posts: {e}")
        return set()
    
    def save_insights(self, insights: List[Dict[str, Any]]):
        """Save insights to JSON file"""
        try:
            # Load existing data
            existing_data = {'insights': [], 'processed_ids': list(self.processed_posts)}
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    existing_data = json.load(f)
            
            # Add new insights
            existing_data['insights'].extend(insights)
            existing_data['processed_ids'] = list(self.processed_posts)
            existing_data['last_updated'] = datetime.now().isoformat()
            
            # Save updated data
            with open(self.data_file, 'w') as f:
                json.dump(existing_data, f, indent=2)
                
            print(f"Saved {len(insights)} new insights to {self.data_file}")
            
        except Exception as e:
            print(f"Error saving insights: {e}")
    
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
        
        # Engagement scoring (upvotes and comments indicate community value)
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
    
    def monitor_subreddit(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Monitor r/claude for new valuable posts"""
        print(f"Monitoring r/{self.subreddit_name}...")
        
        try:
            subreddit = self.reddit.subreddit(self.subreddit_name)
            new_insights = []
            
            # Check recent posts (last 24 hours of hot posts)
            for post in subreddit.hot(limit=limit):
                # Skip if already processed
                if post.id in self.processed_posts:
                    continue
                
                # Calculate relevance
                relevance = self.calculate_relevance_score(post)
                
                # Only include if meets minimum relevance threshold
                if relevance >= self.min_relevance_score:
                    insight = self.extract_insight(post)
                    new_insights.append(insight)
                    print(f"Found valuable post: {post.title[:50]}... (score: {relevance:.2f})")
                
                # Mark as processed
                self.processed_posts.add(post.id)
            
            return new_insights
            
        except Exception as e:
            print(f"Error monitoring subreddit: {e}")
            return []
    
    def generate_summary(self, insights: List[Dict[str, Any]]) -> str:
        """Generate a readable summary of insights"""
        if not insights:
            return "No new valuable insights found in r/claude today."
        
        summary = f"\n🔍 CLAUDE INTELLIGENCE DIGEST - {datetime.now().strftime('%Y-%m-%d')}\n"
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
        
        return summary
    
    def run_daily_check(self):
        """Run the daily monitoring check"""
        print(f"\n🚀 Starting daily r/claude intelligence check at {datetime.now()}")
        
        # Monitor for new insights
        insights = self.monitor_subreddit()
        
        # Save insights
        if insights:
            self.save_insights(insights)
        
        # Generate and display summary
        summary = self.generate_summary(insights)
        print(summary)
        
        # Save summary to file
        summary_file = f"claude_digest_{datetime.now().strftime('%Y%m%d')}.txt"
        with open(summary_file, 'w') as f:
            f.write(summary)
        
        print(f"✅ Daily check complete. Summary saved to {summary_file}")

def main():
    """Main execution function"""
    monitor = RedditClaudeMonitor()
    
    # Check if API credentials are configured
    if not os.getenv('REDDIT_CLIENT_ID'):
        print("❌ Reddit API credentials not configured!")
        print("1. Copy .env.example to .env")
        print("2. Get Reddit API credentials from https://www.reddit.com/prefs/apps")
        print("3. Fill in your credentials in .env file")
        return
    
    try:
        monitor.run_daily_check()
    except Exception as e:
        print(f"❌ Error running monitor: {e}")

if __name__ == "__main__":
    main()