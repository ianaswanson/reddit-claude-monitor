# Reddit Claude Intelligence Monitor - Setup & Usage

## 🎯 What This Does
Automatically monitors r/claude daily, identifies valuable posts using AI-powered content analysis, and delivers a digest of genuinely useful techniques and insights.

## 🚀 Quick Start

### 1. Setup Environment
```bash
cd ~/Development/ai-agent-projects/productivity-tools/reddit-claude-monitor
python3 setup.py
```

### 2. Get Reddit API Credentials
1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Choose "script" as the app type
4. Note your `client_id` (under the app name) and `client_secret`

### 3. Configure Credentials
Edit the `.env` file with your credentials:
```
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=ClaudeIntelligenceMonitor/1.0
```

### 4. Run the Monitor
```bash
# Single run (test)
./reddit_monitor.py

# Scheduled daily runs
python3 run_scheduler.py
```

## 📁 Project Structure
```
reddit-claude-monitor/
├── README.md              # Project overview and architecture
├── INSTRUCTIONS.md         # This file - setup and usage
├── requirements.txt        # Python dependencies
├── setup.py               # Automated setup script
├── .env.example           # Environment variables template
├── .env                   # Your API credentials (created by setup)
├── reddit_monitor.py      # Main monitoring script
├── run_scheduler.py       # Scheduler for daily runs
├── claude_insights.json   # Stored insights and processed post IDs
└── claude_digest_YYYYMMDD.txt  # Daily summary files
```

## 🔧 How It Works

### Content Analysis Algorithm
The monitor evaluates posts using multiple factors:
- **Keywords**: Looks for valuable terms (tip, trick, technique, prompt, workflow, etc.)
- **Engagement**: Higher upvote ratios and comment counts indicate community value
- **Discussion**: Posts with 5+ comments get relevance boost
- **Minimum Threshold**: Only posts scoring 0.7+ relevance are included

### Data Storage
- **JSON File**: Stores all insights and processed post IDs
- **Daily Digests**: Human-readable summaries saved as text files
- **Duplicate Prevention**: Tracks processed posts to avoid repeats

## 🎛️ Configuration Options

Edit `.env` file to customize:
```
SUBREDDIT=claude                    # Subreddit to monitor
CHECK_INTERVAL_HOURS=24            # How often to check
MIN_RELEVANCE_SCORE=0.7            # Minimum score for inclusion (0.0-1.0)
```

## 📊 Output Format

### Daily Digest Example
```
🔍 CLAUDE INTELLIGENCE DIGEST - 2025-08-03
Found 3 valuable posts:

1. Advanced prompting technique for code reviews
   👤 u/claude_expert | ⬆️ 45 | 💬 12
   🔗 https://reddit.com/r/claude/comments/...
   📝 I discovered this technique for getting Claude to provide more thorough code reviews...
   📊 Relevance: 0.85

2. Workflow automation with Claude API
   👤 u/dev_user | ⬆️ 32 | 💬 8
   🔗 https://reddit.com/r/claude/comments/...
   📊 Relevance: 0.78
```

## 🚀 Entrepreneur Features
- **Personal Knowledge Advantage**: Never miss valuable Claude techniques
- **Rapid Iteration**: Easy to adjust filtering algorithms based on results
- **Learning Focus**: Hands-on API integration and content analysis experience

## 🏛️ Government Scaling Potential
- **Team Knowledge Sharing**: Automated AI best practice distribution
- **Training Material**: Curated content for staff AI adoption
- **Compliance**: Add content moderation and approval workflows
- **Integration**: Connect with internal communication systems (Slack, Teams)

## 🛠️ Troubleshooting

### Common Issues
1. **API Credentials Error**: Double-check your Reddit app credentials
2. **Rate Limiting**: Reddit API has limits - the script handles this automatically
3. **No Insights Found**: Try lowering `MIN_RELEVANCE_SCORE` in `.env`

### Debug Mode
Add debugging to see all posts being evaluated:
```python
# In reddit_monitor.py, add this to calculate_relevance_score():
print(f"Evaluating: {post.title[:50]} - Score: {score:.2f}")
```

## 📈 Future Enhancements
- Web dashboard for viewing insights
- Integration with notification systems (email, Slack)
- Machine learning for improved relevance scoring
- Multi-subreddit monitoring
- Export to various formats (CSV, PDF reports)

## 🧠 AI Agent CEO Learning Notes
This project demonstrates:
- **API Integration**: Reddit API with PRAW library
- **Content Analysis**: Automated relevance scoring algorithms
- **Data Persistence**: JSON storage with duplicate prevention
- **Scheduling**: Automated daily monitoring
- **Error Handling**: Robust error management for production use

Perfect foundation for more complex monitoring and analysis systems!