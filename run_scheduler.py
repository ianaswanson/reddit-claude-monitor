#!/usr/bin/env python3
"""
Scheduler for Reddit Claude Intelligence Monitor
Runs the monitor on a schedule (daily by default)
"""

import schedule
import time
import subprocess
import sys
from datetime import datetime
from pathlib import Path

def run_monitor():
    """Run the Reddit monitor"""
    print(f"\n⏰ Scheduled run starting at {datetime.now()}")
    
    try:
        # Run the monitor script
        result = subprocess.run([sys.executable, "reddit_monitor.py"], 
                              capture_output=True, text=True, check=True)
        
        print("✅ Monitor completed successfully")
        print(result.stdout)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Monitor failed: {e}")
        print(f"Error output: {e.stderr}")

def main():
    """Main scheduler function"""
    print("🕐 Starting Reddit Claude Intelligence Monitor Scheduler")
    print("📅 Scheduled to run daily at 9:00 AM")
    print("⚡ Running initial check now...")
    
    # Run immediately on startup
    run_monitor()
    
    # Schedule daily runs
    schedule.every().day.at("09:00").do(run_monitor)
    
    print("\n🔄 Scheduler running. Press Ctrl+C to stop.")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n👋 Scheduler stopped by user")

if __name__ == "__main__":
    main()