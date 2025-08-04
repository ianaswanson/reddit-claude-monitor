#!/usr/bin/env python3
"""
Setup script for Reddit Claude Intelligence Monitor
Handles virtual environment creation and dependency installation
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return None

def setup_project():
    """Set up the project environment"""
    project_dir = Path(__file__).parent
    venv_dir = project_dir / "venv"
    
    print("🚀 Setting up Reddit Claude Intelligence Monitor")
    print(f"📁 Project directory: {project_dir}")
    
    # Create virtual environment
    if not venv_dir.exists():
        run_command(f"python3 -m venv {venv_dir}", "Creating virtual environment")
    else:
        print("✅ Virtual environment already exists")
    
    # Determine pip path
    if sys.platform == "win32":
        pip_path = venv_dir / "Scripts" / "pip"
        python_path = venv_dir / "Scripts" / "python"
    else:
        pip_path = venv_dir / "bin" / "pip"
        python_path = venv_dir / "bin" / "python"
    
    # Install dependencies
    run_command(f"{pip_path} install -r requirements.txt", "Installing Python dependencies")
    
    # Copy .env file if it doesn't exist
    env_file = project_dir / ".env"
    env_example = project_dir / ".env.example"
    
    if not env_file.exists() and env_example.exists():
        run_command(f"cp {env_example} {env_file}", "Creating .env file from template")
        print(f"📝 Please edit {env_file} with your Reddit API credentials")
        print("   Get credentials from: https://www.reddit.com/prefs/apps")
    
    # Make script executable
    script_path = project_dir / "reddit_monitor.py"
    run_command(f"chmod +x {script_path}", "Making script executable")
    
    print("\n🎉 Setup complete!")
    print("\n📋 Next steps:")
    print("1. Get Reddit API credentials: https://www.reddit.com/prefs/apps")
    print("2. Edit .env file with your credentials")
    print("3. Run: ./reddit_monitor.py")
    print("\n💡 To activate virtual environment manually:")
    print(f"   source {venv_dir}/bin/activate  # Mac/Linux")
    print(f"   {venv_dir}\\Scripts\\activate     # Windows")

if __name__ == "__main__":
    setup_project()