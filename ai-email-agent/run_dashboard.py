#!/usr/bin/env python3
"""
Startup script to run both the API and Streamlit dashboard
"""
import subprocess
import sys
import os
import time
import signal
from pathlib import Path

def check_requirements():
    """Check if required packages are installed"""
    required_packages = ['streamlit', 'fastapi', 'uvicorn']
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("Please install them using: pip install -r requirements.txt")
        return False

    return True

def start_api_server():
    """Start the FastAPI server"""
    print("🚀 Starting FastAPI server on http://localhost:8000")

    try:
        # Change to the correct directory
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

        # Start uvicorn server
        api_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn",
            "src.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        return api_process
    except Exception as e:
        print(f"❌ Failed to start API server: {e}")
        return None

def start_dashboard():
    """Start the Streamlit dashboard"""
    print("🎛️ Starting Streamlit dashboard on http://localhost:8501")

    try:
        # Change to the correct directory
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

        # Start streamlit dashboard
        dashboard_process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run",
            "dashboard.py",
            "--server.port", "8502",
            "--server.address", "0.0.0.0"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        return dashboard_process
    except Exception as e:
        print(f"❌ Failed to start dashboard: {e}")
        return None

def wait_for_api_ready(timeout=30):
    """Wait for API server to be ready"""
    import requests

    for _ in range(timeout):
        try:
            response = requests.get("http://localhost:8000/health", timeout=1)
            if response.status_code == 200:
                print("✅ API server is ready!")
                return True
        except:
            pass
        time.sleep(1)

    print("⚠️ API server may not be ready, but continuing...")
    return False

def cleanup_processes(processes):
    """Clean up child processes"""
    print("\n🛑 Shutting down servers...")
    for process in processes:
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
    print("✅ All servers stopped")

def main():
    """Main function to run both servers"""
    print("🤖 AI Email Agent - Starting Dashboard and API Server")
    print("=" * 60)

    # Check requirements
    if not check_requirements():
        sys.exit(1)

    # Check for .env file
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️ .env file not found. Please copy .env.example to .env and configure your settings.")
        print("Example: cp .env.example .env")

        # Ask user if they want to continue
        response = input("Continue anyway? (y/N): ").strip().lower()
        if response != 'y':
            print("Setup cancelled. Please configure .env file first.")
            sys.exit(1)

    processes = []

    try:
        # Start API server
        api_process = start_api_server()
        if not api_process:
            print("❌ Failed to start API server. Exiting...")
            sys.exit(1)

        processes.append(api_process)

        # Wait for API to be ready
        wait_for_api_ready()

        # Start dashboard
        dashboard_process = start_dashboard()
        if not dashboard_process:
            print("❌ Failed to start dashboard. Cleaning up...")
            cleanup_processes(processes)
            sys.exit(1)

        processes.append(dashboard_process)

        print("\n" + "=" * 60)
        print("🎉 Both servers are running!")
        print("📊 Dashboard: http://localhost:8501")
        print("🔗 API Docs:   http://localhost:8000/docs")
        print("❌ Health:     http://localhost:8000/health")
        print("=" * 60)
        print("\nPress Ctrl+C to stop both servers")

        # Setup signal handler for graceful shutdown
        def signal_handler(sig, frame):
            cleanup_processes(processes)
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Wait for processes
        while True:
            # Check if any process has terminated
            for i, process in enumerate(processes):
                if process and process.poll() is not None:
                    print(f"⚠️ Process {i+1} terminated unexpectedly")
                    cleanup_processes(processes)
                    sys.exit(1)

            time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Received interrupt signal")
        cleanup_processes(processes)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        cleanup_processes(processes)
        sys.exit(1)

if __name__ == "__main__":
    main()