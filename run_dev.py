#!/usr/bin/env python3
"""
Unified development server launcher for Flask + React application.
This script starts both the Flask backend and React frontend development servers.
"""

import os
import sys
import subprocess
import signal
import time
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are available."""
    # Check if npm is available
    try:
        subprocess.run(['npm', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ npm is not installed or not in PATH")
        print("Please install Node.js and npm first")
        sys.exit(1)
    
    # Check if Python dependencies are installed
    try:
        import flask
        import flask_cors
        import dotenv
        import pandas
    except ImportError as e:
        print(f"❌ Missing Python dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        sys.exit(1)
    
    print("✅ All dependencies are available")

def install_npm_dependencies():
    """Install npm dependencies if node_modules doesn't exist."""
    app_dir = Path("app")
    node_modules = app_dir / "node_modules"
    
    if not node_modules.exists():
        print("📦 Installing npm dependencies...")
        try:
            subprocess.run(['npm', 'install'], cwd=app_dir, check=True)
            print("✅ npm dependencies installed")
        except subprocess.CalledProcessError:
            print("❌ Failed to install npm dependencies")
            sys.exit(1)
    else:
        print("✅ npm dependencies already installed")

def build_react_app():
    """Build the React application for production."""
    app_dir = Path("app")
    print("🔨 Building React application...")
    
    try:
        subprocess.run(['npm', 'run', 'build'], cwd=app_dir, check=True)
        print("✅ React application built successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to build React application")
        sys.exit(1)

def start_flask_server():
    """Start the Flask server."""
    print("🚀 Starting Flask server...")
    
    # Set environment variables
    env = os.environ.copy()
    env['FLASK_ENV'] = 'development'
    env['FLASK_DEBUG'] = '1'
    
    try:
        flask_process = subprocess.Popen(
            [sys.executable, 'app.py'],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        return flask_process
    except Exception as e:
        print(f"❌ Failed to start Flask server: {e}")
        sys.exit(1)

def start_react_dev_server():
    """Start the React development server."""
    app_dir = Path("app")
    print("🚀 Starting React development server...")
    
    try:
        react_process = subprocess.Popen(
            ['npm', 'run', 'dev'],
            cwd=app_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        return react_process
    except Exception as e:
        print(f"❌ Failed to start React development server: {e}")
        sys.exit(1)

def monitor_processes(flask_process, react_process):
    """Monitor both processes and handle output."""
    print("\n" + "="*60)
    print("🎉 Both servers are starting up!")
    print("📱 React dev server: http://localhost:5173")
    print("🐍 Flask API server: http://localhost:5000")
    print("="*60)
    print("\n💡 Press Ctrl+C to stop both servers\n")
    
    try:
        while True:
            # Check if processes are still running
            flask_poll = flask_process.poll()
            react_poll = react_process.poll()
            
            if flask_poll is not None:
                print(f"❌ Flask server exited with code {flask_poll}")
                break
            
            if react_poll is not None:
                print(f"❌ React server exited with code {react_poll}")
                break
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Shutting down servers...")
        
        # Terminate processes gracefully
        flask_process.terminate()
        react_process.terminate()
        
        # Wait a bit for graceful shutdown
        time.sleep(2)
        
        # Force kill if still running
        if flask_process.poll() is None:
            flask_process.kill()
        if react_process.poll() is None:
            react_process.kill()
        
        print("✅ Servers stopped")

def main():
    """Main function to orchestrate the development environment."""
    print("🚀 Starting Transit Map Development Environment")
    print("=" * 50)
    
    # Check dependencies
    check_dependencies()
    
    # Install npm dependencies if needed
    install_npm_dependencies()
    
    # Ask user which mode they prefer
    print("\nChoose development mode:")
    print("1. Development mode (Flask + React dev server)")
    print("2. Production mode (Flask serves built React app)")
    
    choice = input("Enter choice (1 or 2, default: 1): ").strip()
    
    if choice == "2":
        # Production mode - build React and run only Flask
        build_react_app()
        flask_process = start_flask_server()
        
        print("\n" + "="*60)
        print("🎉 Production server is running!")
        print("🌐 Application: http://localhost:5000")
        print("="*60)
        print("\n💡 Press Ctrl+C to stop the server\n")
        
        try:
            flask_process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Shutting down server...")
            flask_process.terminate()
            time.sleep(2)
            if flask_process.poll() is None:
                flask_process.kill()
            print("✅ Server stopped")
    
    else:
        # Development mode - run both servers
        flask_process = start_flask_server()
        time.sleep(2)  # Give Flask a moment to start
        react_process = start_react_dev_server()
        
        monitor_processes(flask_process, react_process)

if __name__ == "__main__":
    main()