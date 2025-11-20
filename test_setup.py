#!/usr/bin/env python3
"""
Quick test to verify AI Email Agent setup
"""
import os
import subprocess
import sys
from pathlib import Path

def check_directory_structure():
    """Check if all directories and files exist."""
    print("🔍 Checking directory structure...")

    base_path = Path("ai-email-agent")
    if not base_path.exists():
        print("❌ ai-email-agent directory not found!")
        return False

    required_dirs = [
        "src",
        "src/email",
        "src/ai",
        "src/config",
        "src/scheduler",
        "src/utils"
    ]

    required_files = [
        "requirements.txt",
        ".env.example",
        "README.md",
        "dashboard.py",
        "telegram_bot.py",
        "src/main.py",
        "docker-compose.yml"
    ]

    # Check directories
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        if full_path.exists():
            print(f"✅ {dir_path}/")
        else:
            print(f"❌ {dir_path}/ missing!")
            return False

    # Check files
    for file_path in required_files:
        full_path = base_path / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} missing!")
            return False

    return True

def check_dependencies():
    """Check if Python dependencies can be installed."""
    print("\n📦 Checking dependencies...")

    try:
        result = subprocess.run([sys.executable, "-m", "pip", "install", "--dry-run", "-r", "ai-email-agent/requirements.txt"],
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅ All dependencies installable")
            return True
        else:
            print(f"❌ Dependency check failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Dependency check error: {e}")
        return False

def check_env_setup():
    """Check environment setup."""
    print("\n🔧 Checking environment setup...")

    env_file = Path("ai-email-agent/.env")
    env_example = Path("ai-email-agent/.env.example")

    if not env_example.exists():
        print("❌ .env.example missing!")
        return False

    if not env_file.exists():
        print("⚠️ .env file not found. You need to create it:")
        print("   cp ai-email-agent/.env.example ai-email-agent/.env")
        print("   Then edit ai-email-agent/.env with your credentials")
        return False
    else:
        print("✅ .env file exists")
        return True

def main():
    """Run all checks."""
    print("🤖 AI Email Agent Setup Verification")
    print("=" * 50)

    # Change to Data_Analysis directory if needed
    if not Path("ai-email-agent").exists():
        if Path("../Data_Analysis/ai-email-agent").exists():
            os.chdir("../Data_Analysis")
        else:
            print("❌ Cannot find ai-email-agent directory!")
            return False

    all_good = True

    all_good &= check_directory_structure()
    all_good &= check_dependencies()
    all_good &= check_env_setup()

    print("\n" + "=" * 50)
    if all_good:
        print("🎉 Setup looks good!")
        print("\nNext steps:")
        print("1. Edit ai-email-agent/.env with your credentials")
        print("2. Install dependencies: pip install -r ai-email-agent/requirements.txt")
        print("3. Start the API: python ai-email-agent/src/main.py")
        print("4. Start dashboard: python ai-email-agent/run_dashboard.py")
        print("5. Access dashboard at: http://localhost:8502")
    else:
        print("❌ Some issues found. Please fix them before proceeding.")

    return all_good

if __name__ == "__main__":
    main()